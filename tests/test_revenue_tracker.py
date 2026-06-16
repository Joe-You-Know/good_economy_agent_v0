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
            "traceable": True,
            "consent_verified": True,
            "net_of_fees": True,
        })
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
