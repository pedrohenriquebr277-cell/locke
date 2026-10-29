"""Constantes do protocolo entre a interface e o serviço (JSON por linha, TCP em loopback)."""

from __future__ import annotations

import os

HOST = "127.0.0.1"
DEFAULT_PORT = 47653

# Comandos aceitos pelo serviço. Não existe comando de cancelar/parar de propósito.
COMMANDS = ("get_state", "get_config", "save_config", "start_block", "ack_completed")


def port() -> int:
    try:
        return int(os.environ.get("LOCKE_PORT", DEFAULT_PORT))
    except ValueError:
        return DEFAULT_PORT
