from typing import Dict, Any, List
from .models import EthicsDecision


class EthicsGate:
    """Pre-action ethics gate based on adaptive agency.

    In v0, the gate is intentionally strict. Any detected forbidden behavior
    blocks the action because the baseline requires zero negative ethics debt.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.forbidden = set(config.get("forbidden_actions", []))
        self.allowed_categories = set(config.get("allowed_categories", []))
        self.negative_allowed = bool(config.get("negative_ethics_allowed", False))

    def evaluate_action(self, action: Dict[str, Any]) -> EthicsDecision:
        tags = set(action.get("risk_tags", []))
        blocked = sorted(tags.intersection(self.forbidden))

        reasons: List[str] = []
        negative_debt = 0.0

        category = action.get("category")
        if category and category not in self.allowed_categories:
            negative_debt += 0.25
            blocked.append("category_not_allowed")
            reasons.append(f"Category is outside the v0 public-benefit allowlist: {category}")

        if blocked:
            forbidden_blocked = sorted(tags.intersection(self.forbidden))
            if forbidden_blocked:
                negative_debt += 1.0 * len(forbidden_blocked)
                reasons.append(f"Blocked forbidden risk tags: {', '.join(forbidden_blocked)}")

        if action.get("requires_cold_outreach", False) and not self.config.get("cold_outreach_allowed", False):
            negative_debt += 0.5
            blocked.append("cold_outreach")
            reasons.append("Cold outreach is disabled for the clean v0 baseline.")

        if action.get("requires_paid_tool", False) and not self.config.get("paid_tools_allowed_before_revenue", False):
            negative_debt += 0.25
            blocked.append("paid_tool_before_revenue")
            reasons.append("Paid tools are disabled before revenue is earned.")

        if action.get("requires_personal_network", False):
            negative_debt += 0.5
            blocked.append("personal_network_advantage")
            reasons.append("Personal network advantage is outside the v0 start state.")

        if action.get("external_read_action", False) and not self.config.get("read_only_external_apis_allowed", False):
            negative_debt += 0.25
            blocked.append("external_read_action_disabled")
            reasons.append("Read-only external API actions are disabled.")

        if action.get("external_action", False) and not self.config.get("external_write_actions_allowed", False):
            negative_debt += 0.25
            blocked.append("external_write_action_disabled")
            reasons.append("External write actions are disabled until a later reviewed mode.")

        if action.get("collects_personal_data", False) and not action.get("explicit_consent", False):
            negative_debt += 1.0
            blocked.append("personal_data_without_consent")
            reasons.append("Personal data collection requires explicit consent.")

        if action.get("makes_professional_claims", False):
            negative_debt += 1.0
            blocked.append("unsupported_professional_claims")
            reasons.append("Medical, legal, financial, or compliance claims need qualified review.")

        consent = str(action.get("consent_mechanism", "")).lower()
        if action.get("revenue_path") and "opt-in" not in consent and "voluntary" not in consent:
            negative_debt += 0.25
            blocked.append("missing_opt_in_revenue_consent")
            reasons.append("Revenue paths must be opt-in or voluntary.")

        reversibility = str(action.get("reversibility", "")).strip()
        if not reversibility:
            negative_debt += 0.1
            blocked.append("missing_reversibility")
            reasons.append("Action must describe how errors can be corrected or withdrawn.")

        truth_claims = " ".join(str(item).lower() for item in action.get("truth_claims", []))
        risky_truth_terms = ("guarantee", "certified", "official", "legally compliant", "medically safe")
        if any(term in truth_claims for term in risky_truth_terms):
            negative_debt += 0.5
            blocked.append("unsupported_truth_claim")
            reasons.append("Truth claims include terms that need evidence or authority.")

        public_benefit = max(0.0, min(1.0, float(action.get("public_benefit_score", 0.0))))
        evidence_strength = max(0.0, min(1.0, float(action.get("evidence_strength", public_benefit))))
        positive_score = (public_benefit * 0.75) + (evidence_strength * 0.25)

        if action.get("rejects_harmful_shortcuts", False):
            positive_score = min(1.0, positive_score + 0.05)

        allowed = negative_debt == 0.0 or self.negative_allowed

        if allowed and not reasons:
            reasons.append("Allowed: no negative ethics debt detected; action supports adaptive agency.")

        return EthicsDecision(
            allowed=allowed,
            negative_debt=round(negative_debt, 4),
            positive_score=round(positive_score, 4),
            reasons=reasons,
            blocked_categories=blocked,
        )
