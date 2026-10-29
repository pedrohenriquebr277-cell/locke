import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend_mock import MockBackend  # noqa: E402


class MockBackendTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "state.json"
        self.b = MockBackend(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_start_requires_items_and_valid_duration(self):
        self.assertEqual(self.b.start_block(60)["error"], "invalid")
        self.b.save_config(["a.com"], [])
        self.assertEqual(self.b.start_block(0)["error"], "invalid")
        self.assertEqual(self.b.start_block(8 * 3600 + 1)["error"], "invalid")
        self.assertTrue(self.b.start_block(60)["ok"])

    def test_config_locked_while_active_and_persists_ends_at(self):
        self.b.save_config(["a.com"], ["x.exe"])
        self.b.start_block(60)
        self.assertEqual(self.b.save_config([], [])["error"], "block_active")
        again = MockBackend(self.path).get_state()  # "reabrir o app"
        self.assertTrue(again["active"])
        self.assertAlmostEqual(again["ends_at"] - again["server_now"], 60, delta=2)
        self.assertEqual(self.b.start_block(60)["error"], "block_active")

    def test_recents_remembered_after_start(self):
        self.b.save_config(["a.com", "b.com"], ["x.exe"])
        self.b.start_block(1)
        time.sleep(1.1)
        self.b.get_state()
        self.b.save_config(["c.com"], [])
        self.b.start_block(60)
        cfg = self.b.get_config()
        self.assertEqual(cfg["recent_sites"], ["c.com", "a.com", "b.com"])
        self.assertEqual(cfg["recent_apps"], ["x.exe"])

    def test_expiry_then_ack(self):
        self.b.save_config(["a.com"], [])
        self.b.start_block(1)
        time.sleep(1.1)
        st = self.b.get_state()
        self.assertFalse(st["active"])
        self.assertTrue(st["completed"])
        self.assertEqual(st["total_seconds"], 1)
        self.b.ack_completed()
        self.assertFalse(self.b.get_state()["completed"])


if __name__ == "__main__":
    unittest.main()
