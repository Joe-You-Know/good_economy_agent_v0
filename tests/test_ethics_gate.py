import unittest

from agent.ethics_gate import EthicsGate


CONFIG = {
    "allowed_categories": ["education", "accessibility"],
    "forbidden_actions": ["spam", "deception", "fake_traffic"],
    "negative_ethics_allowed": False,
    "cold_outreach_allowed": False,
    "paid_tools_allowed_before_revenue": False,
    "external_actions_allowed": False,
}


class EthicsGateTests(unittest.TestCase):
    def test_clean_action_allowed(self):
        gate = EthicsGate(CONFIG)
        decision = gate.evaluate_action({
            "category": "accessibility",
            "risk_tags": [],
            "requires_cold_outreach": False,
            "requires_paid_tool": False,
            "public_benefit_score": 0.9,
            "evidence_strength": 0.8,
            "consent_mechanism": "voluntary opt-in use",
            "revenue_path": True,
            "reversibility": "can be corrected or withdrawn",
            "truth_claims": ["artifact is free"],
        })
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.negative_debt, 0.0)

    def test_spam_blocked(self):
        gate = EthicsGate(CONFIG)
        decision = gate.evaluate_action({
            "category": "accessibility",
            "risk_tags": ["spam"],
            "requires_cold_outreach": False,
            "requires_paid_tool": False,
            "public_benefit_score": 0.9,
            "consent_mechanism": "voluntary opt-in use",
            "revenue_path": True,
            "reversibility": "can be corrected or withdrawn",
        })
        self.assertFalse(decision.allowed)
        self.assertGreater(decision.negative_debt, 0)

    def test_external_action_blocked_in_baseline(self):
        gate = EthicsGate(CONFIG)
        decision = gate.evaluate_action({
            "category": "education",
            "risk_tags": [],
            "external_action": True,
            "public_benefit_score": 0.7,
            "consent_mechanism": "voluntary opt-in use",
            "revenue_path": True,
            "reversibility": "can be corrected or withdrawn",
        })
        self.assertFalse(decision.allowed)
        self.assertIn("external_write_action_disabled", decision.blocked_categories)


if __name__ == "__main__":
    unittest.main()
