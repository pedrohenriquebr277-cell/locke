import json
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from locke_core import protocol  # noqa: E402
from locke_core.controller import Controller  # noqa: E402
from locke_core.enforcer import Enforcer  # noqa: E402
from locke_core.hosts_manager import BEGIN, HostsManager  # noqa: E402
from locke_core.process_blocker import ProcessBlocker  # noqa: E402
from locke_core.server import Server  # noqa: E402
from locke_core.state_store import StateStore  # noqa: E402

ORIGINAL = "# hosts original\r\n127.0.0.1 localhost\r\n"


class FakeProc:
    def __init__(self, pid, name):
        self.pid, self.info, self.killed = pid, {"name": name}, False

    def kill(self):
        self.killed = True


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.hosts_path = self.dir / "hosts"
        self.hosts_path.write_text(ORIGINAL, newline="")
        self.now = [1000.0]
        self.flushes = []
        self.hosts = HostsManager(self.hosts_path, flush=lambda: self.flushes.append(1))
        self.ctrl = Controller(StateStore(self.dir / "state.json"), clock=lambda: self.now[0],
                               precheck=self.hosts.precheck)
        self.procs = [FakeProc(1, "Discord.exe"), FakeProc(2, "notepad.exe")]
        self.enf = Enforcer(self.ctrl, self.hosts, ProcessBlocker(lambda: self.procs))
        self.ctrl.on_change = self.enf.tick

    def tearDown(self):
        self.tmp.cleanup()

    def hosts_text(self):
        return self.hosts_path.read_bytes().decode("utf-8")


class HostsTest(Base):
    def test_apply_is_idempotent_and_clear_restores_original(self):
        self.assertTrue(self.hosts.apply(["youtube.com"]))
        text = self.hosts_text()
        self.assertIn("0.0.0.0 youtube.com", text)
        self.assertIn("0.0.0.0 www.youtube.com", text)
        self.assertTrue(text.startswith(ORIGINAL.rstrip()))
        self.assertFalse(self.hosts.apply(["youtube.com"]))  # nada muda => sem escrita
        self.assertTrue(self.hosts.clear())
        self.assertEqual(self.hosts_text(), ORIGINAL)
        self.assertFalse(self.hosts.clear())

    def test_apply_replaces_block_and_repairs_tampering(self):
        self.hosts.apply(["a.com"])
        self.hosts.apply(["b.com"])
        self.assertNotIn("a.com", self.hosts_text())
        self.assertEqual(self.hosts_text().count(BEGIN), 1)
        self.hosts_path.write_text(ORIGINAL)  # usuário apaga o bloco
        self.hosts.apply(["b.com"])
        self.assertIn("0.0.0.0 b.com", self.hosts_text())


class EnforcementTest(Base):
    def test_full_session(self):
        self.ctrl.save_config(["youtube.com"], ["discord.exe"])
        self.assertTrue(self.ctrl.start_block(60)["ok"])
        self.assertIn("0.0.0.0 youtube.com", self.hosts_text())  # aplicado já no início
        self.assertTrue(self.procs[0].killed)
        self.assertFalse(self.procs[1].killed)
        self.enf.tick()
        self.now[0] += 61
        self.enf.tick()
        self.assertNotIn(BEGIN, self.hosts_text())
        st = self.ctrl.get_state()
        self.assertTrue(st["completed"])
        self.assertEqual(st["apps_terminated"], 1)

    def test_resume_after_restart_and_cleanup_when_idle(self):
        self.ctrl.save_config(["a.com"], [])
        self.ctrl.start_block(60)
        self.hosts_path.write_text(ORIGINAL)  # serviço reiniciado, hosts adulterado
        self.enf.tick()
        self.assertIn("0.0.0.0 a.com", self.hosts_text())

    def test_validation_and_protected_apps(self):
        self.assertEqual(self.ctrl.save_config(["bad domain\n0.0.0.0 x"], [])["error"], "invalid")
        self.assertEqual(self.ctrl.save_config([], ["explorer.exe"])["error"], "invalid")
        self.assertEqual(self.ctrl.save_config([], ["a.txt"])["error"], "invalid")
        self.assertTrue(self.ctrl.save_config(["A.com", "a.com"], ["X.EXE"])["ok"])
        cfg = self.ctrl.get_config()
        self.assertEqual((cfg["sites"], cfg["apps"]), (["a.com"], ["x.exe"]))

    def test_no_cancel_and_config_locked(self):
        self.ctrl.save_config(["a.com"], [])
        self.ctrl.start_block(60)
        self.assertEqual(self.ctrl.save_config([], [])["error"], "block_active")
        self.assertEqual(self.ctrl.start_block(60)["error"], "block_active")


class FakeGuard:
    def __init__(self, ok=True):
        self.calls, self.ok = [], ok

    def set_locked(self, locked):
        self.calls.append(locked)
        return self.ok


class GuardTest(Base):
    def test_locks_during_session_and_unlocks_after(self):
        guard = FakeGuard()
        enf = Enforcer(self.ctrl, self.hosts, ProcessBlocker(lambda: []), guard)
        self.ctrl.on_change = enf.tick
        enf.tick()
        self.ctrl.save_config(["a.com"], [])
        self.ctrl.start_block(60)
        enf.tick()                      # sem mudança de estado: não chama de novo
        self.now[0] += 61
        enf.tick()
        self.assertEqual(guard.calls, [False, True, False])

    def test_retries_when_guard_fails(self):
        guard = FakeGuard(ok=False)
        enf = Enforcer(self.ctrl, self.hosts, ProcessBlocker(lambda: []), guard)
        enf.tick()
        enf.tick()
        self.assertEqual(guard.calls, [False, False])


class ServerTest(Base):
    def test_roundtrip_and_unknown_command(self):
        server = Server(self.ctrl, port=0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]

        def call(cmd, **args):
            with socket.create_connection((protocol.HOST, port), timeout=2) as s:
                s.sendall((json.dumps({"cmd": cmd, "args": args}) + "\n").encode())
                return json.loads(s.makefile().readline())

        try:
            self.assertTrue(call("save_config", sites=["a.com"], apps=[])["ok"])
            self.assertTrue(call("start_block", duration_seconds=30)["ok"])
            self.assertTrue(call("get_state")["active"])
            self.assertEqual(call("cancel_block")["error"], "invalid")
            self.assertEqual(call("_settle")["error"], "invalid")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
