"""Endurece o próprio serviço durante uma sessão: ninguém (nem administrador) consegue
pará-lo, reconfigurá-lo ou removê-lo pelo gerenciador de serviços até o bloqueio acabar.

Funciona trocando o descritor de segurança do serviço (SDDL) com `sc sdset`, o que só o
SYSTEM consegue fazer enquanto travado. Fora de sessão, volta ao padrão do Windows.
"""

from __future__ import annotations

import logging
import subprocess

log = logging.getLogger("locke")

SERVICE_NAME = "LockeService"

# Direitos: CC consultar config, DC alterar config, LC status, SW dependentes, RP iniciar,
# WP PARAR, DT pausar, LO interrogar, CR controle, SD EXCLUIR, RC ler, WD/WO alterar DACL/dono.
_SYSTEM = "(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;SY)"
_USERS = "(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)"
UNLOCKED = f"D:{_SYSTEM}(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA){_USERS}"   # padrão do Windows
LOCKED = f"D:{_SYSTEM}(A;;CCLCSWRPLOCRRC;;;BA){_USERS}"                 # administradores: sem parar/excluir/alterar


class ServiceGuard:
    def set_locked(self, locked: bool) -> bool:
        """Aplica o SDDL travado/destravado. True se o `sc` aceitou."""
        try:
            res = subprocess.run(["sc.exe", "sdset", SERVICE_NAME, LOCKED if locked else UNLOCKED],
                                 capture_output=True, text=True, timeout=15,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except (OSError, subprocess.SubprocessError):
            log.exception("Falha ao executar sc sdset")
            return False
        if res.returncode != 0:
            log.error("sc sdset falhou (%s): %s", res.returncode, res.stdout.strip())
            return False
        log.info("serviço %s", "travado (não pode ser parado)" if locked else "destravado")
        return True
