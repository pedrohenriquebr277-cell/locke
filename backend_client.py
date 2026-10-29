"""Contrato entre a interface do Locke e o backend.

A interface só conhece esta camada. Para trocar o mock pelo backend real,
implemente `Backend` (ex.: um cliente do serviço do Windows) e altere
`get_backend()` — é o único ponto de troca.

Todas as funções retornam dicts simples. Em caso de falha:
    {"ok": False, "error": "<código>", "message": "<texto opcional>"}
Códigos de erro conhecidos: "service_unavailable", "not_admin",
"block_active", "invalid", "cancelled".
"""

from __future__ import annotations

from typing import Any

Result = dict[str, Any]


class Backend:
    def get_state(self) -> Result:
        """{ok, active, ends_at (epoch s), server_now (epoch s), total_seconds,
        blocked_sites, blocked_apps, completed, apps_terminated | None}.

        `completed` fica True após o fim de um bloqueio, até ack_completed()."""
        raise NotImplementedError

    def get_config(self) -> Result:
        """{ok, sites, apps, recent_sites, recent_apps}

        recent_* são os últimos itens já bloqueados em sessões iniciadas (mais
        recente primeiro), mesmo que tenham sido removidos da lista atual."""
        raise NotImplementedError

    def save_config(self, sites: list[str], apps: list[str]) -> Result:
        """Persiste as listas. Deve recusar (error="block_active") durante um bloqueio."""
        raise NotImplementedError

    def start_block(self, duration_seconds: int) -> Result:
        """Inicia o bloqueio com a configuração salva. O backend decide se aceita."""
        raise NotImplementedError

    def pick_executable(self) -> Result:
        """Abre o seletor de arquivos do Windows. {ok, name} ou error="cancelled"."""
        raise NotImplementedError

    def ack_completed(self) -> Result:
        """Marca a sessão concluída como vista ("Nova sessão")."""
        raise NotImplementedError


def pick_executable_dialog() -> Result:
    """Seletor de .exe do Windows (roda na interface, não no serviço)."""
    import os

    import webview

    if not webview.windows:
        return {"ok": False, "error": "service_unavailable"}
    picked = webview.windows[0].create_file_dialog(
        webview.OPEN_DIALOG,
        file_types=("Aplicativos (*.exe)", "Todos os arquivos (*.*)"),
    )
    if not picked:
        return {"ok": False, "error": "cancelled"}
    return {"ok": True, "name": os.path.basename(picked[0])}


def get_backend() -> Backend:
    """ÚNICO ponto de troca entre o mock e o backend real.

    Por padrão usa o serviço real. Para desenvolver a interface sem o serviço:
    defina LOCKE_BACKEND=mock."""
    import os

    if os.environ.get("LOCKE_BACKEND", "real").lower() == "mock":
        from backend_mock import MockBackend

        return MockBackend()
    from backend_real import RealBackend

    return RealBackend()
