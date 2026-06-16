import tempfile
import unittest
from pathlib import Path

from agent.artifact_builder import ArtifactBuilder
from agent.models import Opportunity


class ArtifactBuilderTests(unittest.TestCase):
    def test_builds_public_artifact_bundle(self):
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
        })

        with tempfile.TemporaryDirectory() as tmp:
            builder = ArtifactBuilder(
                Path(tmp),
                license_text="CC BY 4.0",
                support_links={"donation": "https://example.test/donate"},
            )
            record = builder.build(opportunity)

            self.assertTrue(Path(record.path).exists())
            self.assertEqual(len(record.files), 4)
            artifact_text = Path(record.path).read_text(encoding="utf-8")
            self.assertIn("Small Project Accessibility", artifact_text)
            self.assertIn("do not count as revenue", artifact_text)
            self.assertIn("donation", record.support_links)
            self.assertEqual(record.negative_ethics_debt, 0.0)


if __name__ == "__main__":
    unittest.main()
