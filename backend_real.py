"""Cliente do serviço do Windows do Locke (fala com locke_service.py via TCP em loopback)."""

from __future__ import annotations

import json
import socket

from backend_client import Backend, Result, pick_executable_dialog
from locke_core import protocol


class RealBackend(Backend):
    def _call(self, cmd: str, **args) -> Result:
        try:
            with socket.create_connection((protocol.HOST, protocol.port()), timeout=2) as sock:
                sock.settimeout(5)
                sock.sendall((json.dumps({"cmd": cmd, "args": args}) + "\n").encode("utf-8"))
                buf = b""
                while not buf.endswith(b"\n"):
                    chunk = sock.recv(65536)
                    if not chunk:
                        break
                    buf += chunk
            result = json.loads(buf)
            return result if isinstance(result, dict) else {"ok": False, "error": "service_unavailable"}
        except (OSError, ValueError):
            return {"ok": False, "error": "service_unavailable"}

    def get_state(self) -> Result:
        return self._call("get_state")

    def get_config(self) -> Result:
        return self._call("get_config")

    def save_config(self, sites, apps) -> Result:
        return self._call("save_config", sites=sites, apps=apps)

    def start_block(self, duration_seconds) -> Result:
        return self._call("start_block", duration_seconds=duration_seconds)

    def pick_executable(self) -> Result:
        return pick_executable_dialog()

    def ack_completed(self) -> Result:
        return self._call("ack_completed")
