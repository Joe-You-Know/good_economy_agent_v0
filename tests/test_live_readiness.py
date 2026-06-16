import os
import tempfile
import unittest
from pathlib import Path

from agent.live_readiness import LiveReadiness


CONFIG = {
    "kill_switch_path": "KILL_SWITCH",
    "rate_limit_state_path": "data/rate_limits.json",
    "monitoring_state_path": "data/monitoring_state.json",
    "read_only_external_apis_allowed": True,
    "external_write_actions_allowed": False,
}


class LiveReadinessTests(unittest.TestCase):
    def setUp(self):
        self.old_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.old_env)

    def test_ready_for_read_only_when_no_blockers(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = LiveReadiness(Path(tmp), dict(CONFIG)).evaluate()
            self.assertTrue(report["ready_for_read_only_live_discovery"])
            self.assertFalse(report["ready_for_live_write_actions"])

    def test_kill_switch_blocks_read_only_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "KILL_SWITCH").write_text("stop", encoding="utf-8")
            report = LiveReadiness(root, dict(CONFIG)).evaluate()
            self.assertFalse(report["ready_for_read_only_live_discovery"])
            self.assertIn("Kill switch is active.", report["blockers"])

    def test_donation_url_appears_as_valid_support_path(self):
        os.environ["DONATION_URL"] = "https://example.test/donate"
        with tempfile.TemporaryDirectory() as tmp:
            report = LiveReadiness(Path(tmp), dict(CONFIG)).evaluate()
            self.assertEqual(report["payment"]["valid_support_paths"][0]["label"], "donation")


if __name__ == "__main__":
    unittest.main()
