import tempfile
import unittest
from pathlib import Path

from agent.controls import KillSwitch, KillSwitchTriggered, RateLimiter


class ControlsTests(unittest.TestCase):
    def test_kill_switch_triggers_when_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "KILL_SWITCH").write_text("stop", encoding="utf-8")
            switch = KillSwitch(root, "KILL_SWITCH")
            with self.assertRaises(KillSwitchTriggered):
                switch.assert_not_triggered()

    def test_rate_limiter_blocks_when_window_full(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = [1000.0]
            limiter = RateLimiter(Path(tmp) / "rate.json", clock=lambda: now[0])
            limits = {"minute": {"max_requests": 1, "window_seconds": 60}}
            self.assertTrue(limiter.check("courtlistener", limits)["allowed"])
            limiter.record("courtlistener")
            self.assertFalse(limiter.check("courtlistener", limits)["allowed"])
            now[0] += 61
            self.assertTrue(limiter.check("courtlistener", limits)["allowed"])

    def test_kill_switch_path_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                KillSwitch(Path(tmp), "../outside")


if __name__ == "__main__":
    unittest.main()
