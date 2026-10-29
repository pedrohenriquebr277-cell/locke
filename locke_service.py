"""Serviço do Windows do Locke.

Instalação (como administrador): instalar_servico.ps1
Depuração em console (como administrador): python locke_service.py console
"""

from __future__ import annotations

import sys
import threading

from locke_core import runtime
from locke_core.service_guard import ServiceGuard


def _console() -> None:
    stop = threading.Event()
    print("Locke (console). Ctrl+C para sair.")
    try:
        runtime.run(stop)
    except KeyboardInterrupt:
        stop.set()


if len(sys.argv) > 1 and sys.argv[1] == "console":
    _console()
    sys.exit(0)

import servicemanager  # noqa: E402
import win32event  # noqa: E402
import win32service  # noqa: E402
import win32serviceutil  # noqa: E402


class LockeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "LockeService"
    _svc_display_name_ = "Locke"
    _svc_description_ = "Bloqueia sites e aplicativos durante as sessões de foco do Locke."

    def __init__(self, args):
        super().__init__(args)
        self._stop = threading.Event()
        self._wait = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self._stop.set()
        win32event.SetEvent(self._wait)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("Locke: iniciado")
        runtime.run(self._stop, guard=ServiceGuard())


if __name__ == "__main__":
    if len(sys.argv) == 1:  # iniciado pelo gerenciador de serviços
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(LockeService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(LockeService)
