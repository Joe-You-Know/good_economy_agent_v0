import tempfile
import unittest
from pathlib import Path

from agent.earned_income import EarnedIncomeRunway, classify_github_issue


class EarnedIncomeTests(unittest.TestCase):
    def test_bounty_issue_is_candidate(self):
        candidate = classify_github_issue({
            "title": "Bounty: improve accessibility labels",
            "html_url": "https://github.com/example/repo/issues/1",
            "repository_url": "https://api.github.com/repos/example/repo",
            "labels": ["accessibility", "bounty"],
            "body_excerpt": "Pays $75 after accepted pull request.",
        })
        self.assertTrue(candidate["eligible_for_earned_income_discovery"])
        self.assertEqual(candidate["income_type"], "earned_income")
        self.assertEqual(candidate["expected_liquid_revenue_usd"], 75.0)

    def test_support_only_issue_is_not_revenue_candidate(self):
        candidate = classify_github_issue({
            "title": "Please sponsor this docs project",
            "html_url": "https://github.com/example/repo/issues/2",
            "labels": ["documentation"],
            "body_excerpt": "Donation and sponsorship links are welcome.",
        })
        self.assertFalse(candidate["eligible_for_earned_income_discovery"])
        self.assertEqual(candidate["income_type"], "not_revenue")

    def test_blockchain_bounty_requires_rejection_or_review(self):
        candidate = classify_github_issue({
            "title": "Bounty: document smart contract payment flow",
            "html_url": "https://github.com/example/stellar-wallet/issues/2",
            "repository_url": "https://api.github.com/repos/example/stellar-wallet",
            "labels": ["documentation", "bounty"],
            "body_excerpt": "Pays $250 for accepted work.",
        })
        self.assertFalse(candidate["eligible_for_earned_income_discovery"])
        self.assertIn("smart contract", candidate["risk_signals"])

    def test_token_bounty_requires_rejection_or_review(self):
        candidate = classify_github_issue({
            "title": "MRWK bounty: 150 MRWK - accepted docs requests",
            "html_url": "https://github.com/example/mergework/issues/2",
            "repository_url": "https://api.github.com/repos/example/mergework",
            "labels": ["documentation", "bounty"],
            "body_excerpt": "Reward paid in MRWK.",
        })
        self.assertFalse(candidate["eligible_for_earned_income_discovery"])
        self.assertIn("mrwk", candidate["risk_signals"])

    def test_reward_points_without_money_is_not_candidate(self):
        candidate = classify_github_issue({
            "title": "Achievement system: reward points",
            "html_url": "https://github.com/example/app/issues/4",
            "repository_url": "https://api.github.com/repos/example/app",
            "labels": ["accessibility"],
            "body_excerpt": "Add reward points for users.",
        })
        self.assertFalse(candidate["eligible_for_earned_income_discovery"])
        self.assertIn("reward points", candidate["risk_signals"])

    def test_query_word_does_not_create_bounty_signal(self):
        candidate = classify_github_issue({
            "title": "Workflow selector accessibility",
            "html_url": "https://github.com/example/repo/issues/5",
            "repository_url": "https://api.github.com/repos/example/repo",
            "labels": ["accessibility"],
            "body_excerpt": "Port to accessible select component.",
        }, query="is:issue is:open bounty label:accessibility")
        self.assertFalse(candidate["eligible_for_earned_income_discovery"])
        self.assertEqual(candidate["earned_income_signals"], [])

    def test_unfunded_bounty_backer_prompt_is_not_candidate(self):
        candidate = classify_github_issue({
            "title": "Feature: Internationalize CLI output",
            "html_url": "https://github.com/example/repo/issues/6",
            "repository_url": "https://api.github.com/repos/example/repo",
            "labels": ["accessibility"],
            "body_excerpt": "Want to back this issue? Post a bounty on it.",
        })
        self.assertFalse(candidate["eligible_for_earned_income_discovery"])
        self.assertTrue(candidate["passive_bounty_prompt"])

    def test_runway_writes_reports(self):
        github_results = [{
            "query": "bounty accessibility",
            "ok": True,
            "results": [{
                "title": "Reward: fix accessibility docs",
                "html_url": "https://github.com/example/repo/issues/3",
                "repository_url": "https://api.github.com/repos/example/repo",
                "labels": ["accessibility"],
                "body_excerpt": "Reward: 100 USD for accepted work.",
            }],
        }]
        with tempfile.TemporaryDirectory() as tmp:
            report = EarnedIncomeRunway(Path(tmp)).build_from_github_results(github_results)
            self.assertEqual(report["candidate_count"], 1)
            self.assertTrue((Path(tmp) / "earned_income_runway.json").exists())
            self.assertTrue((Path(tmp) / "earned_income_runway.md").exists())


if __name__ == "__main__":
    unittest.main()
