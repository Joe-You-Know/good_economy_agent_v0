import unittest

from agent.config import ConfigError, validate_config


BASE_CONFIG = {
    "experiment_name": "Good Economy Agent v0",
    "starting_compute_credit_usd": 10.0,
    "starting_economic_cash_usd": 0.0,
    "runtime_limit_cpu_hours": 9,
    "hard_stop_compute_remaining_usd": 0.25,
    "max_single_call_usd": 0.25,
    "max_planning_budget_usd": 1.0,
    "max_search_budget_usd": 1.5,
    "max_build_budget_usd": 4.0,
    "max_publish_budget_usd": 1.0,
    "max_final_report_budget_usd": 0.75,
    "cold_outreach_allowed": False,
    "paid_tools_allowed_before_revenue": False,
    "negative_ethics_allowed": False,
    "allowed_categories": ["education"],
    "forbidden_actions": ["spam"],
    "baseline_revenue_channels": ["voluntary_donation"],
}


class ConfigTests(unittest.TestCase):
    def test_valid_config_gets_defaults(self):
        validated = validate_config(dict(BASE_CONFIG))
        self.assertEqual(validated["openai_assist_model"], "gpt-4.1-mini")
        self.assertFalse(validated["external_actions_allowed"])

    def test_nonzero_starting_cash_rejected_for_v0(self):
        config = dict(BASE_CONFIG)
        config["starting_economic_cash_usd"] = 1.0
        with self.assertRaises(ConfigError):
            validate_config(config)

    def test_negative_ethics_allowed_rejected_for_v0(self):
        config = dict(BASE_CONFIG)
        config["negative_ethics_allowed"] = True
        with self.assertRaises(ConfigError):
            validate_config(config)


if __name__ == "__main__":
    unittest.main()
