import unittest

from agent.live_clients import CourtListenerClient, GitHubClient, OpenLawsClient
from agent.live_clients import _redact_url


class FakeHttp:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get_json(self, url, headers=None, params=None):
        self.calls.append(("GET", url, headers or {}, params or {}))
        return self.response

    def post_form_json(self, url, headers=None, form=None):
        self.calls.append(("POST", url, headers or {}, form or {}))
        return self.response


class LiveClientsTests(unittest.TestCase):
    def test_courtlistener_requires_token(self):
        client = CourtListenerClient("https://example.test/api", token="")
        result = client.search_case_law("test")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "not_configured")

    def test_courtlistener_search_normalizes_results(self):
        http = FakeHttp({
            "ok": True,
            "status": 200,
            "data": {
                "count": 1,
                "results": [{
                    "caseName": "Example v. Test",
                    "court": "Test Court",
                    "dateFiled": "2026-01-01",
                    "citation": ["1 Test 1"],
                    "absolute_url": "/opinion/1/example/",
                    "status": "Published",
                    "opinions": [{"snippet": "<mark>useful</mark>"}],
                }],
            },
        })
        client = CourtListenerClient("https://example.test/api", token="token", http=http)
        result = client.search_case_law("query", page_size=1)
        self.assertTrue(result["ok"])
        self.assertEqual(result["results"][0]["case_name"], "Example v. Test")
        self.assertEqual(result["results"][0]["snippet"], "useful")

    def test_github_search_normalizes_issues(self):
        http = FakeHttp({
            "ok": True,
            "status": 200,
            "data": {
                "total_count": 1,
                "items": [{
                    "title": "Improve docs",
                    "html_url": "https://github.com/example/repo/issues/1",
                    "repository_url": "https://api.github.com/repos/example/repo",
                    "state": "open",
                    "labels": [{"name": "documentation"}],
                    "body": "Bounty: $50 for a clean docs fix.",
                }],
            },
        })
        client = GitHubClient("https://api.github.test", http=http)
        result = client.search_issues("label:documentation", limit=1)
        self.assertTrue(result["ok"])
        self.assertEqual(result["results"][0]["labels"], ["documentation"])
        self.assertIn("Bounty", result["results"][0]["body_excerpt"])

    def test_openlaws_missing_base_url_not_configured(self):
        client = OpenLawsClient("", token="")
        result = client.search("query")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "not_configured")

    def test_redact_url_handles_sensitive_query_params(self):
        redacted = _redact_url("https://example.test/search?api_key=secret&q=public")
        self.assertIn("api_key=REDACTED", redacted)
        self.assertIn("q=public", redacted)


if __name__ == "__main__":
    unittest.main()
