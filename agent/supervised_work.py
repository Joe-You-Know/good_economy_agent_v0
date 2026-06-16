import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .ethics_gate import EthicsGate
from .income_destination import IncomeDestination


DEFAULT_BLOCKED_TARGETS_PATH = "data/blocked_earned_income_targets.json"


class SupervisedWorkRunner:
    """Selects the next earned-income candidate and prepares local work only."""

    def __init__(self, root: Path, config: Dict[str, Any], ledger):
        self.root = Path(root)
        self.config = config
        self.ledger = ledger
        self.output_dir = self.root / "outputs"
        self.work_dir = self.output_dir / "work_packages"
        self.ethics_gate = EthicsGate(config)
        self.income_destination = IncomeDestination(root).load()
        self.blocked_targets = load_blocked_targets(root, config)

    def run(self) -> Dict[str, Any]:
        runway = self._load_runway()
        candidate, rejected = select_candidate(runway.get("candidates", []), self.blocked_targets)
        decision = self._base_decision(runway, candidate, rejected)

        if candidate is None:
            decision.update({
                "status": "no_clean_candidate",
                "selected_candidate": None,
                "next_autonomous_step": "expand_read_only_discovery",
                "reason": (
                    "No candidate currently satisfies the earned-income, public-benefit, "
                    "low-risk, and evidence-readiness filters."
                ),
                "recommended_discovery_queries": self.config.get("earned_income_live_queries", []),
            })
            return self._write_decision(decision)

        if not self.income_destination["configured"]:
            decision.update({
                "status": "blocked_missing_income_destination",
                "selected_candidate": candidate,
                "next_autonomous_step": "configure_earned_income_destination",
                "reason": "The agent cannot start payable work until the earned-income destination is explicit.",
            })
            return self._write_decision(decision)

        ethics = self.ethics_gate.evaluate_action({
            "action_type": "prepare_supervised_earned_income_work",
            "category": "public_documentation",
            "risk_tags": candidate.get("risk_signals", []),
            "external_action": False,
            "requires_cold_outreach": False,
            "requires_paid_tool": False,
            "requires_personal_network": False,
            "collects_personal_data": False,
            "explicit_consent": True,
            "makes_professional_claims": False,
            "public_benefit_score": 0.8,
            "evidence_strength": 0.7,
            "truth_claims": [
                "local preparation only",
                "earned income requires later settlement evidence",
                "support is not revenue",
            ],
            "consent_mechanism": "opt-in work is prepared only for public issue or platform-requested value exchange",
            "revenue_path": True,
            "reversibility": "local work package can be deleted, corrected, or withheld before any external action",
            "rejects_harmful_shortcuts": True,
        })
        self.ledger.append("ethics", {"phase": "supervised_work_selection", **ethics.to_dict()})
        if not ethics.allowed:
            decision.update({
                "status": "blocked_by_ethics_gate",
                "selected_candidate": candidate,
                "ethics": ethics.to_dict(),
                "next_autonomous_step": "reject_candidate_and_expand_discovery",
            })
            return self._write_decision(decision)

        package_paths = self._write_work_package(candidate, ethics.to_dict())
        decision.update({
            "status": "local_work_package_prepared",
            "selected_candidate": candidate,
            "ethics": ethics.to_dict(),
            "work_package": package_paths,
            "next_autonomous_step": "inspect_target_repository_locally_before_external_write",
            "external_write_actions_taken": False,
            "revenue_recorded": False,
            "income_destination": self.income_destination,
        })
        return self._write_decision(decision)

    def _load_runway(self) -> Dict[str, Any]:
        path = self.output_dir / "earned_income_runway.json"
        if not path.exists():
            return {"candidate_count": 0, "candidates": [], "source": "missing_runway"}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"candidate_count": 0, "candidates": []}

    def _base_decision(self, runway: Dict[str, Any], candidate, rejected) -> Dict[str, Any]:
        return {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "supervised-work",
            "runway_candidate_count": len(runway.get("candidates", [])),
            "blocked_target_count": len(self.blocked_targets),
            "rejected_candidates": rejected,
            "supervision_boundary": (
                "The agent may choose and prepare local work. Publishing, claiming work, "
                "submitting pull requests, invoicing, or collecting payment remains a reviewed external write action."
            ),
            "income_destination": self.income_destination,
        }

    def _write_work_package(self, candidate: Dict[str, Any], ethics: Dict[str, Any]) -> Dict[str, str]:
        package_dir = self.work_dir / candidate["candidate_id"]
        package_dir.mkdir(parents=True, exist_ok=True)
        json_path = package_dir / "work_package.json"
        md_path = package_dir / "work_brief.md"
        package = {
            "candidate": candidate,
            "ethics": ethics,
            "local_work_steps": [
                "Clone or inspect the target repository in an ignored workspace.",
                "Read contribution guidance, tests, and issue context.",
                "Make the smallest useful change that satisfies the public request.",
                "Run local validation and record evidence.",
                "Do not submit externally until the supervisor confirms the write action is clean.",
            ],
            "settlement_evidence_needed_later": [
                "accepted work or bounty terms",
                "merged or accepted contribution evidence",
                "payer/platform receipt",
                "net amount after fees",
            ],
            "income_destination": self.income_destination,
        }
        json_path.write_text(json.dumps(package, indent=2, sort_keys=True), encoding="utf-8")
        md_path.write_text(render_work_brief(package), encoding="utf-8")
        return {"json": str(json_path), "markdown": str(md_path)}

    def _write_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = self.output_dir / "supervised_work_decision.json"
        md_path = self.output_dir / "supervised_work_decision.md"
        json_path.write_text(json.dumps(decision, indent=2, sort_keys=True), encoding="utf-8")
        md_path.write_text(render_decision_markdown(decision), encoding="utf-8")
        self.ledger.append("actions", {
            "action": "supervised_work_decision_written",
            "status": decision["status"],
            "selected_candidate_url": (decision.get("selected_candidate") or {}).get("source_url", ""),
            "decision_path": str(md_path),
        })
        return decision


def load_blocked_targets(root: Path, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    relative_path = config.get("blocked_earned_income_targets_path", DEFAULT_BLOCKED_TARGETS_PATH)
    path = (Path(root) / relative_path).resolve()
    root_path = Path(root).resolve()
    if root_path != path and root_path not in path.parents:
        raise ValueError(f"Blocked targets path escapes project root: {relative_path}")
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        targets = data.get("targets", [])
    elif isinstance(data, list):
        targets = data
    else:
        return []
    return [target for target in targets if isinstance(target, dict)]


def select_candidate(candidates: List[Dict[str, Any]], blocked_targets: List[Dict[str, Any]] = None):
    blocked_targets = blocked_targets or []
    rejected = []
    eligible = []
    for candidate in candidates:
        reasons = rejection_reasons(candidate, blocked_targets)
        if reasons:
            rejected.append({
                "candidate_id": candidate.get("candidate_id"),
                "title": candidate.get("title"),
                "source_url": candidate.get("source_url"),
                "reasons": reasons,
            })
        else:
            eligible.append(candidate)

    if not eligible:
        return None, rejected

    eligible.sort(
        key=lambda item: (
            float(item.get("score", 0.0)),
            float(item.get("expected_liquid_revenue_usd", 0.0)),
            item.get("title", ""),
        ),
        reverse=True,
    )
    return eligible[0], rejected


def rejection_reasons(candidate: Dict[str, Any], blocked_targets: List[Dict[str, Any]] = None) -> List[str]:
    reasons = []
    blocked = blocked_target_match(candidate, blocked_targets or [])
    if blocked:
        reason = blocked.get("reason") or "previously blocked target"
        reasons.append(f"blocked external target: {reason}")
    if not candidate.get("eligible_for_earned_income_discovery", False):
        reasons.append("not eligible for earned-income discovery")
    if candidate.get("income_type") != "earned_income":
        reasons.append("not classified as earned income")
    if candidate.get("risk_signals"):
        reasons.append("risk signals require rejection or review")
    if candidate.get("support_inflow_signals"):
        reasons.append("support inflow signal is not revenue")
    if candidate.get("passive_unfunded") or (
        candidate.get("passive_bounty_prompt")
        and float(candidate.get("expected_liquid_revenue_usd", 0.0)) <= 0.0
    ):
        reasons.append("passive bounty/backer prompt is not earned revenue")
    if candidate.get("submitted_pull_requests"):
        reasons.append("funded issue already lists submitted pull requests")
    if candidate.get("in_progress_signal"):
        reasons.append("issue appears already in progress")
    if not candidate.get("source_url"):
        reasons.append("missing source URL")
    if not candidate.get("earned_income_signals"):
        reasons.append("missing issue-side earned-income signal")
    if not candidate.get("public_benefit_signals"):
        reasons.append("missing public-benefit signal")
    if float(candidate.get("expected_liquid_revenue_usd", 0.0)) <= 0.0:
        reasons.append("missing positive parsed earned-income amount")
    return reasons


def blocked_target_match(candidate: Dict[str, Any], blocked_targets: List[Dict[str, Any]]) -> Dict[str, Any]:
    source_url = str(candidate.get("source_url", "")).strip().lower()
    repository_url = str(candidate.get("repository_url", "")).strip().lower()
    candidate_id = str(candidate.get("candidate_id", "")).strip().lower()
    for target in blocked_targets:
        target_source = str(target.get("source_url", "")).strip().lower()
        target_repo = str(target.get("repository_url", "")).strip().lower()
        target_candidate_id = str(target.get("candidate_id", "")).strip().lower()
        if target_source and target_source == source_url:
            return target
        if target_repo and target_repo == repository_url:
            return target
        if target_candidate_id and target_candidate_id == candidate_id:
            return target
    return {}


def render_decision_markdown(decision: Dict[str, Any]) -> str:
    candidate = decision.get("selected_candidate")
    rejected = decision.get("rejected_candidates", [])
    rejected_lines = "\n".join(
        f"- {item.get('title') or item.get('candidate_id')}: {', '.join(item.get('reasons', []))}"
        for item in rejected
    ) or "- none"

    if candidate:
        selected = f"""- Title: {candidate.get("title")}
- Source: {candidate.get("source_url")}
- Score: {candidate.get("score")}
- Expected earned revenue: ${float(candidate.get("expected_liquid_revenue_usd", 0.0)):.2f}
- Signals: {', '.join(candidate.get("earned_income_signals", [])) or 'none'}
"""
    else:
        selected = "- none"

    return f"""# Supervised Work Decision

Generated: {decision["timestamp_utc"]}

## Status

{decision["status"]}

Blocked targets loaded: {decision.get("blocked_target_count", 0)}

## Selected Candidate

{selected}

## Rejected Candidates

{rejected_lines}

## Boundary

{decision["supervision_boundary"]}

## Income Destination

{(decision.get("income_destination") or {}).get("display", "not configured")}

## Next Autonomous Step

{decision.get("next_autonomous_step", "none")}
"""


def render_work_brief(package: Dict[str, Any]) -> str:
    candidate = package["candidate"]
    steps = "\n".join(f"- {item}" for item in package["local_work_steps"])
    evidence = "\n".join(f"- {item}" for item in package["settlement_evidence_needed_later"])
    return f"""# Work Brief

## Candidate

- Title: {candidate.get("title")}
- Source: {candidate.get("source_url")}
- Repository: {candidate.get("repository_url")}
- Expected earned revenue: ${float(candidate.get("expected_liquid_revenue_usd", 0.0)):.2f}
- Income destination: {package["income_destination"]["display"]}

## Local Work Steps

{steps}

## Evidence Needed Before Revenue Counts

{evidence}
"""
