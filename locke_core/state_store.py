"""Armazenamento de estado em JSON, com escrita atômica."""

from __future__ import annotations

import json
from pathlib import Path


class StateStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                data = {}
        except (OSError, ValueError):
            data = {}
        data.setdefault("sites", [])
        data.setdefault("apps", [])
        data.setdefault("recent_sites", [])
        data.setdefault("recent_apps", [])
        data.setdefault("block", None)
        data.setdefault("completed", None)
        return data

    def save(self, data: dict) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)
