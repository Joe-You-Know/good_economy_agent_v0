import tempfile
import unittest
from pathlib import Path

from agent.ledger import JsonlLedger


class LedgerTests(unittest.TestCase):
    def test_append_adds_run_and_record_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = JsonlLedger(Path(tmp), run_id="run_test")
            record = ledger.append("actions", {"action": "test"})
            self.assertEqual(record["run_id"], "run_test")
            self.assertEqual(record["record_id"], "run_test:000001")
            self.assertEqual(ledger.read_all("actions")[0]["action"], "test")


if __name__ == "__main__":
    unittest.main()
