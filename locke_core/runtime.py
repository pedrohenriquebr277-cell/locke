"""Laço principal do serviço: estado + servidor + imposição a cada segundo."""

from __future__ import annotations

import logging
import os
import subprocess
import threading
from pathlib import Path

from .controller import Controller
from .enforcer import Enforcer
from .hosts_manager import HostsManager
from .process_blocker import ProcessBlocker
from .server import Server
from .state_store import StateStore


def default_data_dir() -> Path:
    return Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Locke"


def _lock_down(path: Path) -> None:
    """Só SYSTEM e Administradores escrevem; usuários comuns apenas leem (SIDs: independe do idioma)."""
    try:
        subprocess.run(
            ["icacls", str(path), "/inheritance:r",
             "/grant:r", "*S-1-5-18:(OI)(CI)F", "*S-1-5-32-544:(OI)(CI)F", "*S-1-5-32-545:(OI)(CI)RX"],
            capture_output=True, timeout=15, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        pass


def run(stop: threading.Event, data_dir: Path | None = None, hosts_path: Path | None = None,
        port: int | None = None, guard=None) -> None:
    custom_dir = data_dir is not None
    data_dir = Path(data_dir) if data_dir else default_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    if not custom_dir:
        _lock_down(data_dir)
    logging.basicConfig(filename=str(data_dir / "locke.log"), level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    hosts = HostsManager(hosts_path)
    controller = Controller(StateStore(data_dir / "state.json"), precheck=hosts.precheck)
    enforcer = Enforcer(controller, hosts, ProcessBlocker(), guard)
    controller.on_change = enforcer.tick

    server = Server(controller, port)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logging.info("Serviço Locke iniciado")
    try:
        enforcer.tick()  # retoma uma sessão que estava ativa antes de um reinício
        while not stop.wait(1.0):
            enforcer.tick()
    finally:
        server.shutdown()
        server.server_close()
        logging.info("Serviço Locke encerrado")
