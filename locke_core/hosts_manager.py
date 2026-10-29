"""Edição do arquivo hosts: um bloco marcado, adicionado e removido de forma idempotente."""

from __future__ import annotations

import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Callable

BEGIN = "# >>> LOCKE BEGIN (gerenciado pelo Locke; não edite)"
END = "# <<< LOCKE END"
_BLOCK_RE = re.compile(rf"(?:\r?\n)*{re.escape(BEGIN)}.*?{re.escape(END)}[ \t]*(?:\r?\n)?", re.DOTALL)
_ENC = {"encoding": "utf-8", "errors": "surrogateescape"}  # preserva bytes desconhecidos


def default_hosts_path() -> Path:
    root = os.environ.get("SystemRoot", r"C:\Windows")
    return Path(root) / "System32" / "drivers" / "etc" / "hosts"


def flush_dns() -> None:
    try:
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=10,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        pass


def hostnames(domain: str) -> list[str]:
    return [domain, f"www.{domain}", f"m.{domain}"]


def build_block(sites: list[str]) -> str:
    lines = [BEGIN]
    for site in sites:
        for name in hostnames(site):
            lines.append(f"0.0.0.0 {name}")
            lines.append(f"::1 {name}")
    lines.append(END)
    return "\r\n".join(lines)


def strip_block(text: str) -> str:
    return _BLOCK_RE.sub("", text).rstrip("\r\n")


class HostsManager:
    def __init__(self, path: Path | str | None = None, flush: Callable[[], None] | None = flush_dns):
        self.path = Path(path) if path else default_hosts_path()
        self._flush = flush

    def _read(self) -> str:
        try:
            return self.path.read_bytes().decode(**_ENC)  # bytes: não converte \r\n
        except FileNotFoundError:
            return ""

    def _write(self, text: str) -> None:
        try:
            os.chmod(self.path, stat.S_IWRITE | stat.S_IREAD)  # tira o somente-leitura, se houver
        except OSError:
            pass
        self.path.write_bytes(text.encode(**_ENC))
        if self._flush:
            self._flush()

    def precheck(self) -> dict | None:
        """Erro `not_admin` se o processo não consegue escrever no hosts."""
        try:
            with open(self.path, "ab"):
                pass
        except PermissionError:
            return {"ok": False, "error": "not_admin"}
        except OSError as exc:
            return {"ok": False, "error": "service_unavailable", "message": str(exc)}
        return None

    def apply(self, sites: list[str]) -> bool:
        """Garante que o bloco com `sites` esteja no hosts. True se o arquivo mudou."""
        current = self._read()
        base = strip_block(current)
        parts = [p for p in (base, build_block(sites) if sites else "") if p]
        new = "\r\n\r\n".join(parts) + "\r\n" if parts else ""
        if new == current:
            return False
        self._write(new)
        return True

    def clear(self) -> bool:
        """Remove o bloco do Locke. True se o arquivo mudou."""
        current = self._read()
        if BEGIN not in current:
            return False
        base = strip_block(current)
        self._write(base + "\r\n" if base else "")
        return True
