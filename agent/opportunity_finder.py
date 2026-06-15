import json
from pathlib import Path
from typing import List
from .models import Opportunity


class OpportunityFinder:
    """Finds candidate opportunities.

    v0 uses local seed opportunities so the scaffold is runnable without
    spending API credit or performing external browsing.

    Future live mode can replace this with internet search, GitHub issue
    search, bounty platforms, and opt-in marketplace discovery.
    """

    def __init__(self, data_path: Path):
        self.data_path = Path(data_path)

    def load_seed_opportunities(self) -> List[Opportunity]:
        raw = json.loads(self.data_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list) or not raw:
            raise ValueError("Opportunity seed data must be a non-empty JSON list.")

        opportunities = [Opportunity.from_dict(item) for item in raw]
        seen = set()
        for opportunity in opportunities:
            if opportunity.id in seen:
                raise ValueError(f"Duplicate opportunity id: {opportunity.id}")
            seen.add(opportunity.id)
            _validate_opportunity(opportunity)
        return opportunities


def _validate_opportunity(opportunity: Opportunity) -> None:
    bounded_fields = (
        "public_benefit_score",
        "probability_of_completion",
        "verification_strength",
        "ethics_cleanliness",
        "platform_friction",
        "legal_risk",
    )
    for field in bounded_fields:
        value = float(getattr(opportunity, field))
        if value < 0 or value > 1:
            raise ValueError(f"{opportunity.id}.{field} must be between 0 and 1")

    cost_fields = (
        "expected_liquid_revenue_usd",
        "compute_cost_estimate_usd",
        "runtime_cost_estimate_usd",
    )
    for field in cost_fields:
        value = float(getattr(opportunity, field))
        if value < 0:
            raise ValueError(f"{opportunity.id}.{field} cannot be negative")
