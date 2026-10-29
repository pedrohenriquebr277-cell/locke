"""Encerra processos cujo executável está na lista de apps bloqueados."""

from __future__ import annotations

import os
from typing import Callable, Iterable


def _psutil_processes() -> Iterable:
    import psutil

    return psutil.process_iter(["pid", "name"])


class ProcessBlocker:
    def __init__(self, processes: Callable[[], Iterable] = _psutil_processes):
        self._processes = processes

    def kill(self, exe_names: list[str]) -> set[str]:
        """Encerra os processos que casam (sem diferenciar maiúsculas). Devolve os nomes encerrados."""
        wanted = {n.lower() for n in exe_names}
        killed: set[str] = set()
        if not wanted:
            return killed
        own = os.getpid()
        for proc in self._processes():
            try:
                name = (proc.info.get("name") if hasattr(proc, "info") else proc.name()) or ""
                if name.lower() in wanted and proc.pid != own:
                    proc.kill()
                    killed.add(name.lower())
            except Exception:  # processo já saiu, acesso negado, etc.: tenta de novo no próximo ciclo
                continue
        return killed
