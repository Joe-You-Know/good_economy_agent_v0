import json
import shutil
import tempfile
import unittest
from pathlib import Path

from agent.udemy_lane import build, load_json, validate_package_inputs


REPO_ROOT = Path(__file__).resolve().parents[1]


def make_udemy_lane_root(tmp):
    root = Path(tmp)
    data = root / "data"
    data.mkdir()
    shutil.copyfile(REPO_ROOT / "config.udemy_lane.json", root / "config.udemy_lane.json")
    shutil.copyfile(REPO_ROOT / "data" / "udemy_course_blueprint.json", data / "udemy_course_blueprint.json")
    return root


class UdemyLaneTests(unittest.TestCase):
    def test_builds_local_udemy_package_without_publication_or_revenue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_udemy_lane_root(tmp)
            result = build(root, config_path=root / "config.udemy_lane.json")

            bundle_dir = Path(result["output_dir"])
            manifest = json.loads((bundle_dir / "udemy_submission_manifest.json").read_text(encoding="utf-8"))
            checklist = (bundle_dir / "00_submission_checklist.md").read_text(encoding="utf-8")
            landing = (bundle_dir / "01_udemy_landing_page.md").read_text(encoding="utf-8")
            image_path = bundle_dir / "udemy_course_image_concept.png"

            self.assertEqual(manifest["validation"]["total_planned_video_minutes"], 41.0)
            self.assertEqual(manifest["validation"]["lecture_count"], 6)
            self.assertGreater(manifest["validation"]["description_word_count"], 200)
            self.assertEqual(manifest["course_image"]["width"], 1600)
            self.assertEqual(manifest["course_image"]["height"], 900)
            self.assertTrue(image_path.exists())
            self.assertEqual(image_path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertFalse(manifest["external_actions_performed"])
            self.assertFalse(manifest["udemy_published"])
            self.assertFalse(manifest["payment_collected"])
            self.assertFalse(manifest["revenue_countable_now"])
            self.assertIn("Local package only. Not published to Udemy.", checklist)
            self.assertIn("AI tools were used", landing)
            self.assertIn("There are no student testimonials yet", landing)
            self.assertIn("does not guarantee safety", landing)

    def test_guardrail_regression_blocks_validation(self):
        config = load_json(REPO_ROOT / "config.udemy_lane.json")
        blueprint = load_json(REPO_ROOT / "data" / "udemy_course_blueprint.json")

        unsafe = dict(config)
        unsafe["fake_testimonials_allowed"] = True
        validation = validate_package_inputs(blueprint, unsafe)

        self.assertFalse(validation["allowed"])
        self.assertIn("fake_testimonials_allowed", [check["name"] for check in validation["blocked_checks"]])

    def test_short_course_blocks_validation(self):
        config = load_json(REPO_ROOT / "config.udemy_lane.json")
        blueprint = load_json(REPO_ROOT / "data" / "udemy_course_blueprint.json")
        short_blueprint = dict(blueprint)
        short_blueprint["lectures"] = blueprint["lectures"][:3]

        validation = validate_package_inputs(short_blueprint, config)

        self.assertFalse(validation["allowed"])
        blocked = {check["name"] for check in validation["blocked_checks"]}
        self.assertIn("minimum_video_minutes", blocked)
        self.assertIn("minimum_lecture_count", blocked)


if __name__ == "__main__":
    unittest.main()
