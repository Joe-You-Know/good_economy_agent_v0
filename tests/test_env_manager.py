import os
import tempfile
import unittest
from pathlib import Path

from agent.env_manager import EnvManager


class EnvManagerTests(unittest.TestCase):
    def setUp(self):
        self.old_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.old_env)

    def test_bootstrap_adds_missing_keys_without_removing_existing_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text("OPENAI_API_KEY=secret\n", encoding="utf-8")
            result = EnvManager(root).bootstrap()
            text = (root / ".env").read_text(encoding="utf-8")
            self.assertIn("OPENAI_API_KEY=secret", text)
            self.assertIn("COURTLISTENER_TOKEN=", text)
            self.assertIn("COURTLISTENER_TOKEN", result["added"])

    def test_sync_from_process_does_not_overwrite_existing_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text("COURTLISTENER_TOKEN=existing\n", encoding="utf-8")
            os.environ["COURTLISTENER_TOKEN"] = "new"
            result = EnvManager(root).sync_from_process()
            text = (root / ".env").read_text(encoding="utf-8")
            self.assertIn("COURTLISTENER_TOKEN=existing", text)
            self.assertNotIn("COURTLISTENER_TOKEN=new", text)
            self.assertNotIn("COURTLISTENER_TOKEN", result["changed"])

    def test_report_does_not_display_secret_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text(
                "COURTLISTENER_TOKEN=secret\nDONATION_URL=https://example.test/donate\n",
                encoding="utf-8",
            )
            report = EnvManager(root).report()
            token_entry = next(item for item in report["entries"] if item["name"] == "COURTLISTENER_TOKEN")
            donation_entry = next(item for item in report["entries"] if item["name"] == "DONATION_URL")
            self.assertEqual(token_entry["display_value"], "")
            self.assertEqual(donation_entry["display_value"], "https://example.test/donate")


if __name__ == "__main__":
    unittest.main()
