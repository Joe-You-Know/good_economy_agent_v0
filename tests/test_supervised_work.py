import tempfile
import unittest
from pathlib import Path

from agent.ledger import JsonlLedger
from agent.supervised_work import SupervisedWorkRunner, select_candidate


CONFIG = {
    "allowed_categories": ["public_documentation"],
    "forbidden_actions": ["spam"],
    "negative_ethics_allowed": False,
    "cold_outreach_allowed": False,
    "paid_tools_allowed_before_revenue": False,
    "read_only_external_apis_allowed": True,
    "external_write_actions_allowed": False,
    "earned_income_live_queries": ["IssueHunt accessibility"],
}


class SupervisedWorkTests(unittest.TestCase):
    def test_select_candidate_rejects_empty_or_unclean(self):
        candidate, rejected = select_candidate([
            {
                "candidate_id": "c1",
                "title": "Support only",
                "eligible_for_earned_income_discovery": False,
                "income_type": "not_revenue",
                "source_url": "https://example.test/1",
            }
        ])
        self.assertIsNone(candidate)
        self.assertEqual(len(rejected), 1)

    def test_select_candidate_rejects_missing_amount(self):
        candidate, rejected = select_candidate([
            {
                "candidate_id": "c1",
                "title": "Funded but amount unknown",
                "eligible_for_earned_income_discovery": True,
                "income_type": "earned_income",
                "source_url": "https://example.test/1",
                "earned_income_signals": ["funded"],
                "public_benefit_signals": ["documentation"],
                "expected_liquid_revenue_usd": 0.0,
            }
        ])
        self.assertIsNone(candidate)
        self.assertIn("missing positive parsed earned-income amount", rejected[0]["reasons"])

    def test_select_candidate_rejects_blocked_target(self):
        candidate, rejected = select_candidate(
            [
                {
                    "candidate_id": "c1",
                    "title": "Funded documentation",
                    "source_url": "https://github.com/example/repo/issues/1",
                    "repository_url": "https://api.github.com/repos/example/repo",
                    "eligible_for_earned_income_discovery": True,
                    "income_type": "earned_income",
                    "risk_signals": [],
                    "support_inflow_signals": [],
                    "public_benefit_signals": ["documentation"],
                    "earned_income_signals": ["funded"],
                    "expected_liquid_revenue_usd": 20.0,
                }
            ],
            [
                {
                    "source_url": "https://github.com/example/repo/issues/1",
                    "reason": "repository only accepts collaborator pull requests",
                }
            ],
        )
        self.assertIsNone(candidate)
        self.assertIn("blocked external target", rejected[0]["reasons"][0])

    def test_runner_prepares_package_for_clean_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private = root / "private"
            private.mkdir()
            (private / "income_destination.json").write_text(
                '{"method":"PayPal","account":"person@example.test","currency":"USD"}',
                encoding="utf-8",
            )
            outputs = root / "outputs"
            outputs.mkdir()
            (outputs / "earned_income_runway.json").write_text(
                """{
                  "candidates": [{
                    "candidate_id": "c2",
                    "title": "Funded accessibility doc",
                    "source_url": "https://github.com/example/repo/issues/2",
                    "repository_url": "https://api.github.com/repos/example/repo",
                    "eligible_for_earned_income_discovery": true,
                    "income_type": "earned_income",
                    "risk_signals": [],
                    "support_inflow_signals": [],
                    "public_benefit_signals": ["documentation"],
                    "earned_income_signals": ["bounty"],
                    "expected_liquid_revenue_usd": 25.0,
                    "score": 0.8
                  }]
                }""",
                encoding="utf-8",
            )
            ledger = JsonlLedger(root / "logs", run_id="run_test")
            decision = SupervisedWorkRunner(root, dict(CONFIG), ledger).run()
            self.assertEqual(decision["status"], "local_work_package_prepared")
            self.assertTrue((outputs / "supervised_work_decision.md").exists())
            self.assertTrue((outputs / "work_packages" / "c2" / "work_brief.md").exists())

    def test_runner_refuses_when_no_clean_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outputs = root / "outputs"
            outputs.mkdir()
            (outputs / "earned_income_runway.json").write_text('{"candidates": []}', encoding="utf-8")
            ledger = JsonlLedger(root / "logs", run_id="run_test")
            decision = SupervisedWorkRunner(root, dict(CONFIG), ledger).run()
            self.assertEqual(decision["status"], "no_clean_candidate")

    def test_runner_loads_blocked_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private = root / "private"
            private.mkdir()
            (private / "income_destination.json").write_text(
                '{"method":"PayPal","account":"person@example.test","currency":"USD"}',
                encoding="utf-8",
            )
            data = root / "data"
            data.mkdir()
            (data / "blocked_earned_income_targets.json").write_text(
                """{
                  "targets": [{
                    "repository_url": "https://api.github.com/repos/example/repo",
                    "reason": "repository only accepts collaborator pull requests"
                  }]
                }""",
                encoding="utf-8",
            )
            outputs = root / "outputs"
            outputs.mkdir()
            (outputs / "earned_income_runway.json").write_text(
                """{
                  "candidates": [{
                    "candidate_id": "c2",
                    "title": "Funded docs",
                    "source_url": "https://github.com/example/repo/issues/2",
                    "repository_url": "https://api.github.com/repos/example/repo",
                    "eligible_for_earned_income_discovery": true,
                    "income_type": "earned_income",
                    "risk_signals": [],
                    "support_inflow_signals": [],
                    "public_benefit_signals": ["documentation"],
                    "earned_income_signals": ["funded"],
                    "expected_liquid_revenue_usd": 25.0,
                    "score": 0.8
                  }]
                }""",
                encoding="utf-8",
            )
            ledger = JsonlLedger(root / "logs", run_id="run_test")
            decision = SupervisedWorkRunner(root, dict(CONFIG), ledger).run()
            self.assertEqual(decision["status"], "no_clean_candidate")
            self.assertEqual(decision["blocked_target_count"], 1)
            self.assertIn("blocked external target", decision["rejected_candidates"][0]["reasons"][0])


if __name__ == "__main__":
    unittest.main()
