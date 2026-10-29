"""Aplica o estado ao sistema: hosts, processos e proteção do serviço. Idempotente; chamado a cada segundo."""

from __future__ import annotations

import logging

log = logging.getLogger("locke")


class Enforcer:
    def __init__(self, controller, hosts, blocker, guard=None):
        self._ctrl = controller
        self._hosts = hosts
        self._blocker = blocker
        self._guard = guard          # opcional: trava/destrava o serviço (só no serviço real)
        self._locked: bool | None = None

    def _sync_guard(self, wanted: bool) -> None:
        if self._guard and wanted != self._locked and self._guard.set_locked(wanted):
            self._locked = wanted    # se falhar, tenta de novo no próximo ciclo

    def tick(self) -> None:
        block = self._ctrl.active_block()
        self._sync_guard(bool(block))
        if block:
            try:
                if self._hosts.apply(block["sites"]):
                    log.info("hosts: bloco aplicado (%d sites)", len(block["sites"]))
            except OSError:
                log.exception("Falha ao aplicar o hosts")
            try:
                killed = self._blocker.kill(block["apps"])
                if killed:
                    log.info("processos encerrados: %s", ", ".join(sorted(killed)))
                    self._ctrl.record_terminated(killed)
            except Exception:
                log.exception("Falha ao encerrar processos")
        else:
            try:
                if self._hosts.clear():
                    log.info("hosts: bloco removido (sem bloqueio ativo)")
            except OSError:
                log.exception("Falha ao limpar o hosts")
