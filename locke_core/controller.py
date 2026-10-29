"""Regras de sessão: configuração, início, término. Sem efeitos no sistema.

O fim do bloqueio é sempre um horário absoluto (`ends_at`) guardado no estado.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from typing import Callable

log = logging.getLogger("locke")

MAX_SECONDS = 8 * 3600
MAX_RECENT = 20

_LABEL = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
_DOMAIN = re.compile(rf"^(?:{_LABEL}\.)+(?:[a-z]{{2,}}|xn--[a-z0-9-]+)$")
_EXE = re.compile(r'^[^\\/:*?"<>|\x00-\x1f]{1,124}\.exe$')

# Nunca encerrar processos que derrubariam o Windows ou o próprio Locke.
PROTECTED_EXES = frozenset({
    "explorer.exe", "svchost.exe", "csrss.exe", "winlogon.exe", "lsass.exe",
    "services.exe", "wininit.exe", "smss.exe", "dwm.exe", "taskmgr.exe",
    "locke.exe", "lockeservice.exe",
})


def clean_domain(value: str) -> str | None:
    s = str(value).strip().lower()
    return s if len(s) <= 253 and _DOMAIN.match(s) else None


def clean_exe(value: str) -> str | None:
    s = str(value).strip().lower()
    return s if _EXE.match(s) and s not in PROTECTED_EXES else None


def _dedupe(items: list[str]) -> list[str]:
    seen, out = set(), []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _remember(recent: list[str], used: list[str]) -> list[str]:
    used_set = set(used)
    return (list(used) + [r for r in recent if r not in used_set])[:MAX_RECENT]


class Controller:
    def __init__(self, store, *, clock: Callable[[], float] = time.time,
                 precheck: Callable[[], dict | None] | None = None,
                 on_change: Callable[[], None] | None = None):
        self._store = store
        self._clock = clock
        self._precheck = precheck      # devolve um erro (dict) se o sistema não permite bloquear
        self.on_change = on_change     # chamado após iniciar um bloqueio
        self._lock = threading.RLock()

    # --- uso interno do serviço ---------------------------------------
    def _settle(self, data: dict) -> dict:
        block = data["block"]
        if block and self._clock() >= block["ends_at"]:
            data["completed"] = {
                "total_seconds": block["total_seconds"],
                "apps_terminated": len(set(block.get("terminated_apps", []))),
            }
            data["block"] = None
            self._store.save(data)
            log.info("sessão concluída")
        return data

    def active_block(self) -> dict | None:
        with self._lock:
            return self._settle(self._store.load())["block"]

    def record_terminated(self, names) -> None:
        with self._lock:
            data = self._store.load()
            block = data["block"]
            if not block:
                return
            known = set(block.get("terminated_apps", []))
            if set(names) - known:
                block["terminated_apps"] = sorted(known | set(names))
                self._store.save(data)

    # --- contrato exposto à interface ---------------------------------
    def get_state(self) -> dict:
        with self._lock:
            data = self._settle(self._store.load())
            block, done = data["block"], data["completed"]
            return {
                "ok": True,
                "active": block is not None,
                "ends_at": block["ends_at"] if block else None,
                "server_now": self._clock(),
                "total_seconds": block["total_seconds"] if block else (done or {}).get("total_seconds", 0),
                "blocked_sites": block["sites"] if block else [],
                "blocked_apps": block["apps"] if block else [],
                "completed": done is not None and block is None,
                "apps_terminated": (done or {}).get("apps_terminated"),
            }

    def get_config(self) -> dict:
        with self._lock:
            data = self._store.load()
            return {"ok": True, "sites": data["sites"], "apps": data["apps"],
                    "recent_sites": data["recent_sites"], "recent_apps": data["recent_apps"]}

    def save_config(self, sites: list, apps: list) -> dict:
        with self._lock:
            data = self._settle(self._store.load())
            if data["block"]:
                return {"ok": False, "error": "block_active"}
            if not isinstance(sites, list) or not isinstance(apps, list):
                return {"ok": False, "error": "invalid"}
            good_sites = [clean_domain(s) for s in sites]
            good_apps = [clean_exe(a) for a in apps]
            if None in good_sites or None in good_apps:
                return {"ok": False, "error": "invalid", "message": "Algum item da lista não é válido."}
            data["sites"] = _dedupe(good_sites)
            data["apps"] = _dedupe(good_apps)
            self._store.save(data)
            return {"ok": True}

    def start_block(self, duration_seconds) -> dict:
        with self._lock:
            data = self._settle(self._store.load())
            if data["block"]:
                return {"ok": False, "error": "block_active"}
            if (isinstance(duration_seconds, bool) or not isinstance(duration_seconds, (int, float))
                    or not 0 < duration_seconds <= MAX_SECONDS):
                return {"ok": False, "error": "invalid", "message": "Duração fora do limite."}
            if not data["sites"] and not data["apps"]:
                return {"ok": False, "error": "invalid", "message": "Nada para bloquear."}
            if self._precheck and (err := self._precheck()):
                return err
            seconds = int(duration_seconds)
            data["block"] = {
                "ends_at": self._clock() + seconds,
                "total_seconds": seconds,
                "sites": list(data["sites"]),
                "apps": list(data["apps"]),
                "terminated_apps": [],
            }
            data["completed"] = None
            data["recent_sites"] = _remember(data["recent_sites"], data["sites"])
            data["recent_apps"] = _remember(data["recent_apps"], data["apps"])
            self._store.save(data)
        log.info("sessão iniciada: %ds, %d sites, %d apps", seconds, len(data["sites"]), len(data["apps"]))
        if self.on_change:
            self.on_change()
        return {"ok": True}

    def ack_completed(self) -> dict:
        with self._lock:
            data = self._store.load()
            data["completed"] = None
            self._store.save(data)
            return {"ok": True}
