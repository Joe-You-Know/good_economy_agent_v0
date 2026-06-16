import os
import tempfile
import unittest
from pathlib import Path

from agent.ledger import JsonlLedger
from agent.live_discovery import LiveDiscovery


class FakeHttp:
    def get_json(self, url, headers=None, params=None):
        if "github" in url:
            return {
                "ok": True,
                "status": 200,
                "data": {
                    "total_count": 1,
                    "items": [{
                        "title": "Bounty: fix accessibility docs",
                        "html_url": "https://github.com/example/repo/issues/1",
                        "repository_url": "https://api.github.com/repos/example/repo",
                        "labels": [{"name": "accessibility"}],
                        "body": "Pays $50 after accepted work.",
                    }],
                },
            }
        return {"ok": True, "status": 200, "data": {"count": 0, "results": []}}

    def post_form_json(self, url, headers=None, form=None):
        return {"ok": True, "status": 200, "data": []}


CONFIG = {
    "allowed_categories": ["public_documentation"],
    "forbidden_actions": ["spam"],
    "negative_ethics_allowed": False,
    "cold_outreach_allowed": False,
    "paid_tools_allowed_before_revenue": False,
    "read_only_external_apis_allowed": True,
    "external_write_actions_allowed": False,
    "kill_switch_path": "KILL_SWITCH",
    "rate_limit_state_path": "data/rate_limits.json",
    "github_api_base_url": "https://api.github.test",
    "github_rate_limits": {"minute": {"max_requests": 10, "window_seconds": 60}},
    "courtlistener_api_base_url": "https://courtlistener.test/api/rest/v4",
    "courtlistener_rate_limits": {"minute": {"max_requests": 10, "window_seconds": 60}},
    "openlaws_api_base_url": "https://openlaws.test",
    "openlaws_rate_limits": {"minute": {"max_requests": 10, "window_seconds": 60}},
    "github_live_queries": ["is:issue is:open label:documentation"],
    "earned_income_live_queries": ["is:issue is:open bounty"],
    "earned_income_candidate_limit": 5,
    "legal_precedent_queries": ["test legal query"],
    "live_discovery_query_limit": 1,
    "openai_assist_timeout_seconds": 1,
}


class LiveDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.old_env = dict(os.environ)
        os.environ["COURTLISTENER_TOKEN"] = "token"

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.old_env)

    def test_live_discovery_writes_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            ledger = JsonlLedger(root / "logs", run_id="run_test")
            discovery = LiveDiscovery(root, dict(CONFIG), ledger)
            discovery.http = FakeHttp()
            snapshot = discovery.run()
            self.assertEqual(snapshot["mode"], "live-discovery")
            self.assertEqual(snapshot["earned_income"]["candidate_count"], 1)
            self.assertTrue((root / "outputs" / "live_discovery_snapshot.json").exists())
            self.assertTrue((root / "outputs" / "earned_income_runway.md").exists())


if __name__ == "__main__":
    unittest.main()
