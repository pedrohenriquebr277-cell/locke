"""Locke — interface. Uso: python main.py [--teste]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import webview

from api import Api
from backend_client import get_backend


def resource_path(relative: str) -> str:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return str(base / relative)


def main() -> None:
    parser = argparse.ArgumentParser(prog="Locke")
    parser.add_argument("--teste", action="store_true", help="duração padrão de 1 minuto")
    args = parser.parse_args()

    api = Api(get_backend(), test_mode=args.teste)
    webview.create_window(
        "Locke",
        resource_path("web/index.html"),
        js_api=api,
        width=760,
        height=860,
        min_size=(480, 640),
        background_color="#1c1c1a",
        frameless=True,
        easy_drag=False,  # só a barra superior arrasta a janela
    )
    webview.start(debug=False, icon=resource_path("icon.ico"))


if __name__ == "__main__":
    main()
