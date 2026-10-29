"""Backend MOCK: mesmas regras do serviço, mas sem bloquear nada no sistema.

Só para desenvolver/validar a interface (LOCKE_BACKEND=mock)."""

from __future__ import annotations

import os
from pathlib import Path

from backend_client import Backend, Result, pick_executable_dialog
from locke_core.controller import Controller
from locke_core.state_store import StateStore


def _data_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "Locke"


class MockBackend(Backend):
    def __init__(self, path: Path | None = None):
        self._ctrl = Controller(StateStore(path or (_data_dir() / "mock_state.json")))

    def _simulated_error(self) -> Result | None:
        mode = os.environ.get("LOCKE_MOCK_ERROR", "").lower()
        if mode == "service":
            return {"ok": False, "error": "service_unavailable"}
        if mode == "admin":
            return {"ok": False, "error": "not_admin"}
        return None

    def get_state(self) -> Result:
        return self._simulated_error() or self._ctrl.get_state()

    def get_config(self) -> Result:
        return self._simulated_error() or self._ctrl.get_config()

    def save_config(self, sites, apps) -> Result:
        return self._simulated_error() or self._ctrl.save_config(sites, apps)

    def start_block(self, duration_seconds) -> Result:
        return self._simulated_error() or self._ctrl.start_block(duration_seconds)

    def pick_executable(self) -> Result:
        return pick_executable_dialog()

    def ack_completed(self) -> Result:
        return self._ctrl.ack_completed()
