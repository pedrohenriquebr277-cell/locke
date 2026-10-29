"""Servidor TCP em loopback (JSON por linha) que expõe o Controller à interface."""

from __future__ import annotations

import json
import socketserver

from . import protocol


class _Handler(socketserver.StreamRequestHandler):
    timeout = 5

    def handle(self) -> None:
        try:
            req = json.loads(self.rfile.readline(65536))
            cmd = req["cmd"]
            if cmd not in protocol.COMMANDS:
                raise ValueError(cmd)
            result = getattr(self.server.controller, cmd)(**(req.get("args") or {}))
        except Exception:
            result = {"ok": False, "error": "invalid"}
        self.wfile.write((json.dumps(result) + "\n").encode("utf-8"))


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, controller, port: int | None = None):
        super().__init__((protocol.HOST, protocol.port() if port is None else port), _Handler)
        self.controller = controller
