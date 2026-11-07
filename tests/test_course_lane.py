import json
import shutil
import tempfile
import unittest
from pathlib import Path

from agent.course_lane import build, ethics_check, load_json


REPO_ROOT = Path(__file__).resolve().parents[1]


def make_course_lane_root(tmp):
    root = Path(tmp)
    data = root / "data"
    data.mkdir()
    shutil.copyfile(REPO_ROOT / "config.course_lane.json", root / "config.course_lane.json")
    shutil.copyfile(REPO_ROOT / "data" / "course_opportunities.json", data / "course_opportunities.json")
    return root


class CourseLaneTests(unittest.TestCase):
    def test_builds_local_only_bundle_without_countable_revenue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_course_lane_root(tmp)
            result = build(root, config_path=root / "config.course_lane.json")

            bundle_dir = Path(result["bundle_dir"])
            manifest = json.loads((bundle_dir / "bundle_manifest.json").read_text(encoding="utf-8"))
            report = (bundle_dir / "final_course_lane_report.md").read_text(encoding="utf-8")
            landing = (bundle_dir / "landing_page_beta.md").read_text(encoding="utf-8")

            self.assertEqual(manifest["course"]["course_id"], "claude_code_safety_hooks")
            self.assertFalse(manifest["external_actions_performed"])
            self.assertFalse(manifest["payment_collected"])
            self.assertFalse(manifest["revenue_countable_now"])
            self.assertIn("$0.00", report)
            self.assertIn("None.", report)
            self.assertIn("This course does not guarantee safety.", landing)
            self.assertNotIn("This guarantees safety.", landing)
            self.assertNotIn(".**.", landing)
            self.assertNotIn("\u00e2", landing)
            self.assertNotIn("\u2014", report)

    def test_course_lane_guardrails_default_to_no_external_sales_actions(self):
        config = load_json(REPO_ROOT / "config.course_lane.json")

        self.assertFalse(config["external_actions_allowed"])
        self.assertFalse(config["cold_outreach_allowed"])
        self.assertFalse(config["fake_urgency_allowed"])
        self.assertFalse(config["earnings_claims_allowed"])
        self.assertFalse(config["testimonials_allowed_without_real_student_use"])

    def test_ethics_check_rejects_marketing_guardrail_regression(self):
        config = load_json(REPO_ROOT / "config.course_lane.json")
        opportunity = load_json(REPO_ROOT / "data" / "course_opportunities.json")[0]

        clean = ethics_check(opportunity, config)
        self.assertTrue(clean["allowed"])
        self.assertEqual(clean["negative_debt"], 0.0)

        unsafe_config = dict(config)
        unsafe_config["fake_urgency_allowed"] = True
        unsafe = ethics_check(opportunity, unsafe_config)
        self.assertFalse(unsafe["allowed"])
        self.assertGreater(unsafe["negative_debt"], 0.0)
        self.assertIn("fake_urgency_allowed", unsafe["blocked_categories"])


if __name__ == "__main__":
    unittest.main()
