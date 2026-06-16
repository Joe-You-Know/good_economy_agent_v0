import unittest

from agent.revenue_tracker import RevenueTracker


class RevenueTrackerTests(unittest.TestCase):
    def test_clean_traceable_revenue_valid(self):
        tracker = RevenueTracker()
        result = tracker.validate_revenue_event({
            "amount_usd": 5.0,
            "source": "public-good bounty",
            "caused_by_action_id": "run:000001",
            "classification": "clean",
            "income_type": "earned_income",
            "value_exchange": True,
            "evidence": ["accepted bounty receipt", "merged pull request"],
            "destination": "PayPal: payout@recipient.test (USD)",
            "traceable": True,
            "consent_verified": True,
            "net_of_fees": True,
        })
        self.assertTrue(result["valid"])

    def test_self_payment_invalid(self):
        tracker = RevenueTracker()
        result = tracker.validate_revenue_event({
            "amount_usd": 5.0,
            "source": "operator",
            "caused_by_action_id": "run:000001",
            "classification": "clean",
            "income_type": "earned_income",
            "value_exchange": True,
            "evidence": ["accepted bounty receipt"],
            "destination": "PayPal: payout@recipient.test (USD)",
            "traceable": True,
            "consent_verified": True,
            "net_of_fees": True,
            "self_payment": True,
        })
        self.assertFalse(result["valid"])

    def test_zero_amount_invalid_as_revenue(self):
        tracker = RevenueTracker()
        result = tracker.validate_revenue_event({
            "amount_usd": 0.0,
            "source": "none",
            "caused_by_action_id": "run:000001",
            "classification": "clean",
            "income_type": "earned_income",
            "value_exchange": True,
            "evidence": ["accepted bounty receipt"],
            "destination": "PayPal: payout@recipient.test (USD)",
            "traceable": True,
            "consent_verified": True,
            "net_of_fees": True,
        })
        self.assertFalse(result["valid"])

    def test_donation_invalid_as_revenue(self):
        tracker = RevenueTracker()
        result = tracker.validate_revenue_event({
            "amount_usd": 5.0,
            "source": "supporter",
            "caused_by_action_id": "run:000001",
            "classification": "clean",
            "income_type": "donation",
            "value_exchange": False,
            "evidence": ["support receipt"],
            "destination": "PayPal: payout@recipient.test (USD)",
            "traceable": True,
            "consent_verified": True,
            "net_of_fees": True,
        })
        self.assertFalse(result["valid"])
        self.assertIn("not earned revenue", result["reason"])

    def test_value_exchange_required_for_revenue(self):
        tracker = RevenueTracker()
        result = tracker.validate_revenue_event({
            "amount_usd": 5.0,
            "source": "goodwill supporter",
            "caused_by_action_id": "run:000001",
            "classification": "clean",
            "income_type": "earned_income",
            "value_exchange": False,
            "evidence": ["support receipt"],
            "destination": "PayPal: payout@recipient.test (USD)",
            "traceable": True,
            "consent_verified": True,
            "net_of_fees": True,
        })
        self.assertFalse(result["valid"])

    def test_settlement_evidence_required(self):
        tracker = RevenueTracker()
        result = tracker.validate_revenue_event({
            "amount_usd": 5.0,
            "source": "public-good bounty",
            "caused_by_action_id": "run:000001",
            "classification": "clean",
            "income_type": "earned_income",
            "value_exchange": True,
            "evidence": [],
            "destination": "PayPal: payout@recipient.test (USD)",
            "traceable": True,
            "consent_verified": True,
            "net_of_fees": True,
        })
        self.assertFalse(result["valid"])
        self.assertIn("settlement evidence", result["reason"])

    def test_template_placeholder_rejected(self):
        tracker = RevenueTracker()
        result = tracker.validate_revenue_event({
            "amount_usd": 5.0,
            "source": "TEMPLATE - replace with real payer",
            "caused_by_action_id": "run:record-id-for-the-accepted-work",
            "classification": "clean",
            "income_type": "earned_income",
            "value_exchange": True,
            "evidence": ["URL or receipt proving payment"],
            "destination": "PayPal: payout@recipient.test (USD)",
            "traceable": True,
            "consent_verified": True,
            "net_of_fees": True,
        })
        self.assertFalse(result["valid"])
        self.assertIn("template placeholders", result["reason"])

    def test_destination_required(self):
        tracker = RevenueTracker()
        result = tracker.validate_revenue_event({
            "amount_usd": 5.0,
            "source": "public-good bounty",
            "caused_by_action_id": "run:000001",
            "classification": "clean",
            "income_type": "earned_income",
            "value_exchange": True,
            "evidence": ["accepted bounty receipt"],
            "traceable": True,
            "consent_verified": True,
            "net_of_fees": True,
        })
        self.assertFalse(result["valid"])
        self.assertIn("destination", result["reason"])


if __name__ == "__main__":
    unittest.main()
