import tempfile
import unittest
from pathlib import Path

from agent.income_destination import IncomeDestination


class IncomeDestinationTests(unittest.TestCase):
    def test_loads_private_income_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private = root / "private"
            private.mkdir()
            (private / "income_destination.json").write_text(
                '{"method":"PayPal","account":"person@example.test","currency":"USD"}',
                encoding="utf-8",
            )
            destination = IncomeDestination(root).load()
            self.assertTrue(destination["configured"])
            self.assertEqual(destination["display"], "PayPal: person@example.test (USD)")

    def test_missing_destination_not_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = IncomeDestination(Path(tmp), env={}).load()
            self.assertFalse(destination["configured"])


if __name__ == "__main__":
    unittest.main()
