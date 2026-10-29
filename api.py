"""Ponte fina entre o JavaScript (js_api) e o backend_client."""

from __future__ import annotations

from backend_client import Backend, Result


class Api:
    def __init__(self, backend: Backend, test_mode: bool = False):
        self._backend = backend
        self._test_mode = test_mode
        self._maximized = False
        self._fullscreen = False

    def _window(self):
        import webview

        return webview.windows[0] if webview.windows else None

    def win_minimize(self) -> Result:
        if (win := self._window()):
            win.minimize()
        return {"ok": True}

    def win_toggle_maximize(self) -> Result:
        if (win := self._window()):
            win.restore() if self._maximized else win.maximize()
            self._maximized = not self._maximized
        return {"ok": True, "maximized": self._maximized}

    def win_toggle_fullscreen(self) -> Result:
        if (win := self._window()):
            win.toggle_fullscreen()
            self._fullscreen = not self._fullscreen
        return {"ok": True, "fullscreen": self._fullscreen}

    def win_close(self) -> Result:
        if (win := self._window()):
            win.destroy()
        return {"ok": True}

    def _guard(self, fn, *args) -> Result:
        try:
            return fn(*args)
        except Exception as exc:  # qualquer falha de comunicação vira estado de erro na UI
            return {"ok": False, "error": "service_unavailable", "message": str(exc)}

    def app_info(self) -> Result:
        return {"ok": True, "test_mode": self._test_mode}

    def get_state(self) -> Result:
        return self._guard(self._backend.get_state)

    def get_config(self) -> Result:
        return self._guard(self._backend.get_config)

    def save_config(self, sites, apps) -> Result:
        return self._guard(self._backend.save_config, list(sites), list(apps))

    def start_block(self, duration_seconds) -> Result:
        return self._guard(self._backend.start_block, duration_seconds)

    def pick_executable(self) -> Result:
        return self._guard(self._backend.pick_executable)

    def ack_completed(self) -> Result:
        return self._guard(self._backend.ack_completed)
