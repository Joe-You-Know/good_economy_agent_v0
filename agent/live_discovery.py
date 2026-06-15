import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .controls import KillSwitch, RateLimiter
from .ethics_gate import EthicsGate
from .ledger import JsonlLedger
from .live_clients import CourtListenerClient, GitHubClient, LiveHttpClient, OpenLawsClient


class LiveDiscovery:
    def __init__(self, root: Path, config: Dict[str, Any], ledger: JsonlLedger):
        self.root = Path(root)
        self.config = config
        self.ledger = ledger
        self.output_dir = self.root / "outputs"
        self.kill_switch = KillSwitch(self.root, config["kill_switch_path"])
        self.rate_limiter = RateLimiter(self.root / config["rate_limit_state_path"])
        self.ethics_gate = EthicsGate(config)
        self.http = LiveHttpClient(timeout_seconds=int(config.get("openai_assist_timeout_seconds", 30)))

    def run(self) -> Dict[str, Any]:
        if not self.config.get("read_only_external_apis_allowed", False):
            raise RuntimeError("Read-only external API calls are disabled in config.")
        self.kill_switch.assert_not_triggered()

        ethics = self.ethics_gate.evaluate_action({
            "action_type": "read_only_live_discovery",
            "category": "public_documentation",
            "risk_tags": [],
            "external_read_action": True,
            "external_action": False,
            "requires_cold_outreach": False,
            "requires_paid_tool": False,
            "requires_personal_network": False,
            "collects_personal_data": False,
            "explicit_consent": True,
            "makes_professional_claims": False,
            "public_benefit_score": 0.8,
            "evidence_strength": 0.7,
            "truth_claims": ["read-only public API discovery", "no legal advice", "no publication"],
            "consent_mechanism": "uses public or authenticated API access under provider terms",
            "revenue_path": False,
            "reversibility": "local logs and snapshots can be deleted or superseded",
            "rejects_harmful_shortcuts": True,
        })
        self.ledger.append("ethics", {"phase": "live_discovery", **ethics.to_dict()})
        if not ethics.allowed:
            raise RuntimeError(f"Ethics gate blocked live discovery: {ethics.reasons}")

        snapshot = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "live-discovery",
            "github": self._discover_github(),
            "courtlistener": self._check_courtlistener(),
            "openlaws": self._check_openlaws(),
            "external_write_actions": "disabled",
        }
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "live_discovery_snapshot.json"
        path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
        self.ledger.append("actions", {
            "action": "live_discovery_snapshot_written",
            "path": str(path),
            "github_queries": len(snapshot["github"]),
            "courtlistener_queries": len(snapshot["courtlistener"]),
            "openlaws_queries": len(snapshot["openlaws"]),
        })
        return snapshot

    def _discover_github(self) -> List[Dict[str, Any]]:
        client = GitHubClient(
            self.config["github_api_base_url"],
            token=os.environ.get("GITHUB_TOKEN", ""),
            http=self.http,
        )
        results = []
        for query in self.config.get("github_live_queries", []):
            allowed = self.rate_limiter.check("github", self.config["github_rate_limits"])
            if not allowed["allowed"]:
                results.append({"query": query, "ok": False, "rate_limited": allowed})
                continue
            response = client.search_issues(query, limit=int(self.config["live_discovery_query_limit"]))
            self.rate_limiter.record("github")
            self.ledger.append("actions", {
                "action": "github_issue_search",
                "query": query,
                "ok": response.get("ok"),
                "status": response.get("status"),
                "count": response.get("count"),
            })
            results.append({"query": query, **response})
        return results

    def _check_courtlistener(self) -> List[Dict[str, Any]]:
        client = CourtListenerClient(
            self.config["courtlistener_api_base_url"],
            token=os.environ.get("COURTLISTENER_TOKEN", ""),
            http=self.http,
        )
        results = []
        for query in self.config.get("legal_precedent_queries", []):
            allowed = self.rate_limiter.check("courtlistener", self.config["courtlistener_rate_limits"])
            if not allowed["allowed"]:
                results.append({"query": query, "ok": False, "rate_limited": allowed})
                continue
            response = client.search_case_law(
                query,
                page_size=int(self.config["live_discovery_query_limit"]),
                semantic=False,
            )
            if response.get("status") != "not_configured":
                self.rate_limiter.record("courtlistener")
            self.ledger.append("actions", {
                "action": "courtlistener_case_law_search",
                "query": query,
                "ok": response.get("ok"),
                "status": response.get("status"),
                "count": response.get("count"),
            })
            results.append({"query": query, **response})
        return results

    def _check_openlaws(self) -> List[Dict[str, Any]]:
        base_url = os.environ.get("OPENLAWS_API_BASE_URL") or self.config.get("openlaws_api_base_url", "")
        client = OpenLawsClient(
            base_url,
            token=os.environ.get("OPENLAWS_API_KEY", ""),
            http=self.http,
        )
        results = []
        for query in self.config.get("legal_precedent_queries", []):
            allowed = self.rate_limiter.check("openlaws", self.config["openlaws_rate_limits"])
            if not allowed["allowed"]:
                results.append({"query": query, "ok": False, "rate_limited": allowed})
                continue
            response = client.search(query, limit=int(self.config["live_discovery_query_limit"]))
            if response.get("status") != "not_configured":
                self.rate_limiter.record("openlaws")
            self.ledger.append("actions", {
                "action": "openlaws_search",
                "query": query,
                "ok": response.get("ok"),
                "status": response.get("status"),
                "count": response.get("count"),
            })
            results.append({"query": query, **response})
        return results
