import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


DEFAULT_ASSET_SOURCE_PATHS = [
    r"C:\ConstructiveRT",
    r"C:\Users\josep\OneDrive\Documents\Causal Impedance Model\papers\pdf",
]

THEME_PATTERNS = {
    "constructivert_browser_extension": (
        "constructivert chrome",
        "browser extension",
        "manifest.json",
    ),
    "constructive_runtime_tools": (
        "constructive runtime",
        "constructive rt",
        "constructive daily",
        "deep cleanup",
        "breathing layer",
        "router extender",
    ),
    "cim_research_library": (
        "causal impedance",
        "causal imped",
        "cim",
        "physics",
        "primitive measure",
        "constructive shell",
        "prime frontier",
        "riemann",
    ),
    "cryptography_adjacent_research": (
        "sha256",
        "sha-256",
        "secp",
        "elliptic",
        "ecdllp",
        "ecdlp",
        "bitcoin",
        "hash",
    ),
}

THEME_PROFILES = {
    "constructivert_browser_extension": {
        "title": "ConstructiveRT browser extension package",
        "revenue_paths": ["product_sale", "license_fee", "paid_service_contract"],
        "public_benefit_signals": ["resource_efficiency", "truthful_decision_making", "durable_human_capability"],
        "local_next_steps": [
            "Identify the newest release package and source folder.",
            "Create a local product brief with features, limits, screenshots needed, and install instructions.",
            "Prepare a private QA checklist before any marketplace or Chrome Web Store submission.",
        ],
        "score": 0.82,
    },
    "constructive_runtime_tools": {
        "title": "Constructive runtime and cleanup tooling bundle",
        "revenue_paths": ["paid_service_contract", "license_fee", "product_sale"],
        "public_benefit_signals": ["resource_efficiency", "small_business_resilience", "public_documentation"],
        "local_next_steps": [
            "Bundle the newest stable scripts and reports into a clean local offer outline.",
            "Draft a paid service package for read-only diagnostics and reversible cleanup planning.",
            "Add warnings against destructive cleanup without review.",
        ],
        "score": 0.78,
    },
    "cim_research_library": {
        "title": "Causal Impedance Model research library",
        "revenue_paths": ["license_fee", "product_sale", "paid_service_contract"],
        "public_benefit_signals": ["education", "open_science", "scientific_reproducibility"],
        "local_next_steps": [
            "Create a local catalog of papers by theme and maturity.",
            "Draft a paid research digest or licensing brief with cautious, non-professional claims.",
            "Separate exploratory theory from verified implementation results.",
        ],
        "score": 0.74,
    },
    "cryptography_adjacent_research": {
        "title": "Cryptography-adjacent research and tooling",
        "revenue_paths": ["license_fee", "paid_service_contract"],
        "public_benefit_signals": ["education", "scientific_reproducibility"],
        "local_next_steps": [
            "Inventory claims and remove any unsupported security, investment, or guaranteed-performance language.",
            "Prepare a research-only licensing brief before any paid offer.",
            "Require human review before contacting any security, crypto, or financial buyer.",
        ],
        "score": 0.52,
        "risk_signals": ["security_claims_require_review", "crypto_adjacent_claims_require_review"],
    },
}


class AssetIncomeRunway:
    """Builds a read-only local runway from owned assets to earned-income paths."""

    def __init__(self, root: Path, config: Dict[str, Any], ledger=None):
        self.root = Path(root)
        self.config = config
        self.ledger = ledger
        self.output_dir = self.root / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> Dict[str, Any]:
        source_paths = self.config.get("asset_income_source_paths", DEFAULT_ASSET_SOURCE_PATHS)
        inventory = inventory_asset_sources(
            source_paths,
            max_items_per_source=int(self.config.get("asset_income_max_items_per_source", 80)),
        )
        candidates = build_asset_candidates(inventory)
        report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "asset-discovery",
            "source_paths": list(source_paths),
            "inventory": inventory,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "income_boundary": (
                "Owned assets may support earned income through product sales, license fees, "
                "paid service contracts, or marketplace sales. Support, donations, grants, gifts, "
                "and patronage still do not count as revenue."
            ),
            "trading_boundary": trading_boundary(self.config),
            "write_action_boundary": (
                "This mode is read-only. Creating listings, sending offers, executing trades, "
                "connecting payment, or publishing claims requires fresh approval."
            ),
        }
        self.write_report(report)
        if self.ledger:
            self.ledger.append("actions", {
                "action": "asset_income_runway_written",
                "candidate_count": len(candidates),
                "source_count": len(inventory),
                "path": str(self.output_dir / "asset_income_runway.md"),
            })
        return report

    def write_report(self, report: Dict[str, Any]) -> Dict[str, str]:
        json_path = self.output_dir / "asset_income_runway.json"
        md_path = self.output_dir / "asset_income_runway.md"
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        md_path.write_text(render_asset_runway_markdown(report), encoding="utf-8")
        return {"json_path": str(json_path), "markdown_path": str(md_path)}


class AssetWorkRunner:
    """Prepares a local product/service package from the current asset runway."""

    def __init__(self, root: Path, config: Dict[str, Any], ledger=None):
        self.root = Path(root)
        self.config = config
        self.ledger = ledger
        self.output_dir = self.root / "outputs"
        self.work_dir = self.output_dir / "asset_work"

    def run(self) -> Dict[str, Any]:
        runway = self._load_runway()
        candidate = select_asset_candidate(runway.get("candidates", []))
        decision = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "asset-work",
            "candidate_count": len(runway.get("candidates", [])),
            "selected_candidate": candidate,
            "external_write_actions_taken": False,
            "revenue_recorded": False,
        }
        if not candidate:
            decision.update({
                "status": "no_asset_candidate",
                "reason": "No asset candidate is available. Run asset-discovery first.",
                "next_autonomous_step": "run_asset_discovery",
            })
            return self._write_decision(decision)

        paths = self._write_package(candidate)
        approval_request = self._write_approval_request(candidate, paths)
        decision.update({
            "status": "local_asset_work_package_prepared",
            "work_package": paths,
            "approval_request": approval_request,
            "next_autonomous_step": "review_product_brief_and_approve_listing_or_payment_setup",
            "approval_needed_for": [
                "creating a public listing",
                "publishing an extension or product page",
                "connecting payment",
                "sending offers or sales messages",
                "making performance, security, legal, financial, or scientific claims",
            ],
        })
        if self.ledger:
            self.ledger.append("actions", {
                "action": "asset_work_package_prepared",
                "candidate_id": candidate["candidate_id"],
                "title": candidate["title"],
                "path": paths["brief"],
            })
        return self._write_decision(decision)

    def _load_runway(self) -> Dict[str, Any]:
        path = self.output_dir / "asset_income_runway.json"
        if not path.exists():
            return {"candidate_count": 0, "candidates": []}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"candidate_count": 0, "candidates": []}

    def _write_package(self, candidate: Dict[str, Any]) -> Dict[str, str]:
        package_dir = self.work_dir / candidate["candidate_id"]
        package_dir.mkdir(parents=True, exist_ok=True)
        brief_path = package_dir / "product_brief.md"
        checklist_path = package_dir / "qa_checklist.md"
        approval_path = package_dir / "approval_needed.md"
        brief_path.write_text(render_asset_product_brief(candidate), encoding="utf-8")
        checklist_path.write_text(render_asset_qa_checklist(candidate), encoding="utf-8")
        approval_path.write_text(render_asset_approval_request(candidate, brief_path), encoding="utf-8")
        return {
            "brief": str(brief_path),
            "qa_checklist": str(checklist_path),
            "approval_needed": str(approval_path),
        }

    def _write_approval_request(self, candidate: Dict[str, Any], paths: Dict[str, str]) -> Dict[str, str]:
        approval_dir = self.output_dir / "approval_requests"
        approval_dir.mkdir(parents=True, exist_ok=True)
        request = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
            "kind": "asset_external_write_review",
            "summary": f"Good Economy Agent prepared a local product package for: {candidate['title']}",
            "requested_action": (
                "Approve or deny the next external step: create a public listing/payment setup plan "
                "for this asset. No listing, payment connection, or outbound message will be performed "
                "without approval."
            ),
            "evidence_path": paths["brief"],
            "risk_note": (
                "External listing or payment setup could create public claims and commercial obligations. "
                "Review QA, licensing, and claims boundaries first."
            ),
            "external_write_action": True,
            "requires_fresh_user_approval": True,
        }
        json_path = approval_dir / "latest.json"
        md_path = approval_dir / "latest.md"
        json_path.write_text(json.dumps(request, indent=2, sort_keys=True), encoding="utf-8")
        md_path.write_text(render_pending_asset_approval(request), encoding="utf-8")
        return {"json": str(json_path), "markdown": str(md_path)}

    def _write_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = self.output_dir / "asset_work_decision.json"
        md_path = self.output_dir / "asset_work_decision.md"
        json_path.write_text(json.dumps(decision, indent=2, sort_keys=True), encoding="utf-8")
        md_path.write_text(render_asset_work_decision(decision), encoding="utf-8")
        return decision


def inventory_asset_sources(source_paths: Iterable[str], max_items_per_source: int = 80) -> List[Dict[str, Any]]:
    inventory = []
    for raw_path in source_paths:
        path = Path(raw_path)
        source = {
            "path": str(path),
            "exists": path.exists(),
            "items": [],
            "error": "",
        }
        if not path.exists():
            source["error"] = "path does not exist"
            inventory.append(source)
            continue
        try:
            children = sorted(path.iterdir(), key=lambda item: item.name.lower())
        except OSError as exc:
            source["error"] = str(exc)
            inventory.append(source)
            continue
        for child in children[:max_items_per_source]:
            source["items"].append(_asset_item(child))
        source["truncated"] = len(children) > max_items_per_source
        source["item_count_seen"] = len(children)
        inventory.append(source)
    return inventory


def build_asset_candidates(inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for source in inventory:
        for item in source.get("items", []):
            for theme in classify_asset_item(item):
                grouped[theme].append({**item, "source_root": source.get("path", "")})

    candidates = []
    for theme, items in grouped.items():
        profile = THEME_PROFILES[theme]
        risk_signals = list(profile.get("risk_signals", []))
        candidates.append({
            "candidate_id": _candidate_id(theme + "|" + "|".join(item["path"] for item in items[:5])),
            "source": "local_assets",
            "theme": theme,
            "title": profile["title"],
            "asset_count": len(items),
            "representative_assets": _representative_assets(items),
            "income_type": "earned_income_path",
            "revenue_paths": list(profile["revenue_paths"]),
            "expected_liquid_revenue_usd": 0.0,
            "score": _score_asset_candidate(float(profile["score"]), len(items), risk_signals),
            "public_benefit_signals": list(profile["public_benefit_signals"]),
            "risk_signals": risk_signals,
            "eligible_for_local_preparation": True,
            "requires_review_before_external_action": True,
            "local_next_steps": list(profile["local_next_steps"]),
        })
    return sorted(candidates, key=lambda candidate: candidate["score"], reverse=True)


def select_asset_candidate(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    eligible = [
        candidate for candidate in candidates
        if candidate.get("eligible_for_local_preparation", False)
    ]
    if not eligible:
        return {}
    eligible.sort(
        key=lambda candidate: (
            not bool(candidate.get("risk_signals")),
            float(candidate.get("score", 0.0)),
            int(candidate.get("asset_count", 0)),
        ),
        reverse=True,
    )
    return eligible[0]


def classify_asset_item(item: Dict[str, Any]) -> List[str]:
    text = _normalize(item.get("name", "") + " " + item.get("path", ""))
    themes = []
    for theme, patterns in THEME_PATTERNS.items():
        if any(pattern in text for pattern in patterns):
            themes.append(theme)
    return themes


def trading_boundary(config: Dict[str, Any]) -> Dict[str, Any]:
    policy = dict(config.get("trading_policy", {}))
    real_money_allowed = bool(policy.get("real_money_trading_allowed", False))
    return {
        "paper_trading_allowed": bool(policy.get("paper_trading_allowed", True)),
        "real_money_trading_allowed": real_money_allowed,
        "status": "real_money_trading_disabled" if not real_money_allowed else "requires_fresh_approval",
        "allowed_local_actions": [
            "read-only market research",
            "paper-trade simulation",
            "risk-model drafting",
            "strategy backtest with no live orders",
        ],
        "blocked_without_fresh_approval": [
            "placing trades",
            "connecting brokerage accounts",
            "moving funds",
            "claiming investment performance",
            "giving personalized financial advice",
        ],
    }


def render_asset_runway_markdown(report: Dict[str, Any]) -> str:
    candidate_lines = []
    for index, candidate in enumerate(report.get("candidates", []), start=1):
        assets = "\n".join(
            f"  - {item['name']} ({item['kind']})"
            for item in candidate.get("representative_assets", [])
        ) or "  - none"
        steps = "\n".join(f"  - {step}" for step in candidate.get("local_next_steps", []))
        candidate_lines.append(f"""### {index}. {candidate["title"]}

- Theme: {candidate["theme"]}
- Score: {candidate["score"]}
- Asset count: {candidate["asset_count"]}
- Revenue paths: {", ".join(candidate["revenue_paths"])}
- Public-benefit signals: {", ".join(candidate["public_benefit_signals"])}
- Risk signals: {", ".join(candidate["risk_signals"]) or "none"}
- External action review required: {candidate["requires_review_before_external_action"]}

Representative assets:
{assets}

Local next steps:
{steps}
""")

    candidates = "\n".join(candidate_lines) or "No local asset candidates found."
    trading = report["trading_boundary"]
    return f"""# Asset Income Runway

Generated: {report["timestamp_utc"]}

## Boundary

{report["income_boundary"]}

{report["write_action_boundary"]}

## Trading Boundary

- Paper trading allowed: {trading["paper_trading_allowed"]}
- Real-money trading allowed: {trading["real_money_trading_allowed"]}
- Status: {trading["status"]}

Real-money trading, brokerage connection, and live orders require fresh approval and a written risk policy.

## Candidates

{candidates}
"""


def render_asset_product_brief(candidate: Dict[str, Any]) -> str:
    assets = "\n".join(
        f"- {item['name']} ({item['kind']}): `{item['path']}`"
        for item in candidate.get("representative_assets", [])
    ) or "- none"
    revenue_paths = "\n".join(f"- {path}" for path in candidate.get("revenue_paths", []))
    next_steps = "\n".join(f"- {step}" for step in candidate.get("local_next_steps", []))
    return f"""# Product Brief

## Working Offer

{candidate["title"]}

## Revenue Paths

{revenue_paths}

## Public Benefit

{", ".join(candidate.get("public_benefit_signals", [])) or "none"}

## Representative Assets

{assets}

## Positioning Draft

Package this as a practical, opt-in tool or service for improving local productivity, resource efficiency, documentation quality, or research reproducibility. Avoid inflated claims. The first paid path should be a small, honest value exchange: a productized package, a license, or a scoped paid service based on assets already owned by the operator.

## Local Next Steps

{next_steps}

## Claims Boundary

- Do not claim guaranteed income, trading performance, security breakthroughs, legal compliance, medical effect, or financial advice.
- Do not publish, list, email, invoice, or connect payment without approval.
- Use cautious language until the asset has a fresh QA pass and review.
"""


def render_asset_qa_checklist(candidate: Dict[str, Any]) -> str:
    return f"""# QA Checklist

Candidate: {candidate["title"]}

- [ ] Confirm the newest package or source folder.
- [ ] Verify install or usage instructions locally.
- [ ] Identify license ownership and third-party dependencies.
- [ ] Remove unsupported claims.
- [ ] Add clear limitations and support boundaries.
- [ ] Confirm payment destination before any paid listing.
- [ ] Confirm no donation, patronage, sponsorship, grant, or gift is counted as revenue.
- [ ] Get approval before any external write action.
"""


def render_asset_approval_request(candidate: Dict[str, Any], brief_path: Path) -> str:
    return f"""# Approval Needed Before External Action

Candidate: {candidate["title"]}

Review the local product brief:

`{brief_path}`

Approval is required before:

- creating a public listing,
- publishing a Chrome extension or product page,
- connecting PayPal or another payment method,
- sending offers,
- making claims about performance, security, law, finance, science, or trading.
"""


def render_pending_asset_approval(request: Dict[str, Any]) -> str:
    return f"""# Pending Approval Request

Generated: {request["timestamp_utc"]}

## Summary

{request["summary"]}

## Requested Action

{request["requested_action"]}

## Evidence

{request["evidence_path"]}

## Risk Note

{request["risk_note"]}
"""


def render_asset_work_decision(decision: Dict[str, Any]) -> str:
    candidate = decision.get("selected_candidate") or {}
    paths = decision.get("work_package") or {}
    return f"""# Asset Work Decision

Generated: {decision["timestamp_utc"]}

## Status

{decision["status"]}

## Selected Candidate

{candidate.get("title", "none")}

## Work Package

- Brief: {paths.get("brief", "none")}
- QA checklist: {paths.get("qa_checklist", "none")}
- Approval note: {paths.get("approval_needed", "none")}

## Boundary

External write actions taken: {decision.get("external_write_actions_taken", False)}
Revenue recorded: {decision.get("revenue_recorded", False)}

## Next Step

{decision.get("next_autonomous_step", "none")}
"""


def _asset_item(path: Path) -> Dict[str, Any]:
    try:
        stat = path.stat()
        size = int(stat.st_size) if path.is_file() else 0
        modified = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
    except OSError:
        size = 0
        modified = ""
    return {
        "name": path.name,
        "path": str(path),
        "kind": "directory" if path.is_dir() else "file",
        "extension": path.suffix.lower(),
        "size_bytes": size,
        "modified_utc": modified,
    }


def _representative_assets(items: List[Dict[str, Any]], limit: int = 8) -> List[Dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (item.get("modified_utc", ""), item.get("name", "")),
        reverse=True,
    )[:limit]


def _score_asset_candidate(base_score: float, asset_count: int, risk_signals: List[str]) -> float:
    score = base_score + min(asset_count, 12) * 0.01
    if risk_signals:
        score -= 0.18
    return round(max(0.0, min(score, 0.95)), 3)


def _candidate_id(value: str) -> str:
    import hashlib

    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"asset_income_{digest}"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).replace("_", " ").replace("-", " ")).lower()
