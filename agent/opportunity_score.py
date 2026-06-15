from typing import Any, Dict

from .models import Opportunity


def score_opportunity(opp: Opportunity, config: Dict[str, Any] = None) -> float:
    return explain_opportunity_score(opp, config)["score"]


def explain_opportunity_score(opp: Opportunity, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Scores opportunity under zero-negative-ethics baseline.

    This is not pure revenue maximization. It prioritizes:
    - public benefit,
    - completion probability,
    - verification,
    - ethics cleanliness,
    - low cost,
    - low legal/platform friction.
    """
    config = config or {}
    public_benefit = _clamp01(opp.public_benefit_score)
    completion = _clamp01(opp.probability_of_completion)
    verification = _clamp01(opp.verification_strength)
    ethics = _clamp01(opp.ethics_cleanliness)

    gross = (
        (opp.expected_liquid_revenue_usd + 1.0)
        * public_benefit
        * completion
        * verification
        * ethics
    )

    costs = (
        opp.compute_cost_estimate_usd
        + opp.runtime_cost_estimate_usd
        + opp.platform_friction
        + opp.legal_risk
    )

    penalties = 0.0
    penalty_reasons = []

    allowed_categories = set(config.get("allowed_categories", []))
    if allowed_categories and opp.category not in allowed_categories:
        penalties += 100.0
        penalty_reasons.append("category_not_allowed")

    forbidden = set(config.get("forbidden_actions", []))
    forbidden_tags = sorted(set(opp.risk_tags or []).intersection(forbidden))
    if forbidden_tags:
        penalties += 100.0 * len(forbidden_tags)
        penalty_reasons.append(f"forbidden_risk_tags:{','.join(forbidden_tags)}")

    if opp.legal_risk >= 0.5:
        penalties += 5.0
        penalty_reasons.append("high_legal_risk")

    score = round(gross - costs - penalties, 6)
    return {
        "score": score,
        "gross_value": round(gross, 6),
        "cost_penalty": round(costs, 6),
        "safety_penalty": round(penalties, 6),
        "penalty_reasons": penalty_reasons,
        "factors": {
            "expected_liquid_revenue_usd": opp.expected_liquid_revenue_usd,
            "public_benefit_score": public_benefit,
            "probability_of_completion": completion,
            "verification_strength": verification,
            "ethics_cleanliness": ethics,
            "compute_cost_estimate_usd": opp.compute_cost_estimate_usd,
            "runtime_cost_estimate_usd": opp.runtime_cost_estimate_usd,
            "platform_friction": opp.platform_friction,
            "legal_risk": opp.legal_risk,
        },
    }


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
