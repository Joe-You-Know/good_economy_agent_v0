import unittest

from agent.models import Opportunity
from agent.opportunity_score import explain_opportunity_score, score_opportunity


class OpportunityScoreTests(unittest.TestCase):
    def test_clean_public_good_scores_positive(self):
        opportunity = Opportunity.from_dict({
            "id": "accessibility_checklist",
            "title": "Accessibility checklist",
            "category": "accessibility",
            "expected_liquid_revenue_usd": 0.0,
            "public_benefit_score": 0.9,
            "probability_of_completion": 0.9,
            "verification_strength": 0.8,
            "ethics_cleanliness": 1.0,
            "compute_cost_estimate_usd": 0.05,
            "runtime_cost_estimate_usd": 0.0,
            "platform_friction": 0.05,
            "legal_risk": 0.01,
            "description": "A useful free artifact.",
            "risk_tags": [],
        })
        score = score_opportunity(opportunity, {"allowed_categories": ["accessibility"]})
        self.assertGreater(score, 0)

    def test_forbidden_risk_tags_apply_safety_penalty(self):
        opportunity = Opportunity.from_dict({
            "id": "bad",
            "title": "Spammy thing",
            "category": "accessibility",
            "expected_liquid_revenue_usd": 10.0,
            "public_benefit_score": 0.9,
            "probability_of_completion": 0.9,
            "verification_strength": 0.8,
            "ethics_cleanliness": 1.0,
            "compute_cost_estimate_usd": 0.05,
            "runtime_cost_estimate_usd": 0.0,
            "platform_friction": 0.05,
            "legal_risk": 0.01,
            "description": "Looks profitable but harmful.",
            "risk_tags": ["spam"],
        })
        explanation = explain_opportunity_score(opportunity, {
            "allowed_categories": ["accessibility"],
            "forbidden_actions": ["spam"],
        })
        self.assertLess(explanation["score"], 0)
        self.assertIn("forbidden_risk_tags:spam", explanation["penalty_reasons"])


if __name__ == "__main__":
    unittest.main()
