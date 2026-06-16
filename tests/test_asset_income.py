import tempfile
import unittest
from pathlib import Path

from agent.asset_income import (
    AssetIncomeRunway,
    AssetWorkRunner,
    build_asset_candidates,
    inventory_asset_sources,
    select_asset_candidate,
    trading_boundary,
)


class AssetIncomeTests(unittest.TestCase):
    def test_inventory_and_candidate_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ConstructiveRT_Chrome_v0_1_14.zip").write_text("zip placeholder", encoding="utf-8")
            (root / "constructive_runtime_v0_7_transfer_boundary_profiler.zip").write_text(
                "zip placeholder",
                encoding="utf-8",
            )
            (root / "Causal_Impedance_Model_Complete.pdf").write_text("pdf placeholder", encoding="utf-8")

            inventory = inventory_asset_sources([str(root)])
            candidates = build_asset_candidates(inventory)
            themes = {candidate["theme"] for candidate in candidates}
            self.assertIn("constructivert_browser_extension", themes)
            self.assertIn("constructive_runtime_tools", themes)
            self.assertIn("cim_research_library", themes)

    def test_report_writes_asset_runway(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "assets"
            source.mkdir()
            (source / "ConstructiveRT_Chrome_v0_1_14.zip").write_text("zip placeholder", encoding="utf-8")
            report = AssetIncomeRunway(
                root,
                {
                    "asset_income_source_paths": [str(source)],
                    "asset_income_max_items_per_source": 10,
                    "trading_policy": {"paper_trading_allowed": True, "real_money_trading_allowed": False},
                },
            ).run()
            self.assertEqual(report["candidate_count"], 1)
            self.assertTrue((root / "outputs" / "asset_income_runway.json").exists())
            self.assertTrue((root / "outputs" / "asset_income_runway.md").exists())

    def test_trading_boundary_blocks_real_money_by_default(self):
        boundary = trading_boundary({})
        self.assertTrue(boundary["paper_trading_allowed"])
        self.assertFalse(boundary["real_money_trading_allowed"])
        self.assertEqual(boundary["status"], "real_money_trading_disabled")

    def test_select_asset_candidate_prefers_unflagged_high_score(self):
        selected = select_asset_candidate([
            {
                "title": "Risky",
                "eligible_for_local_preparation": True,
                "score": 0.95,
                "asset_count": 10,
                "risk_signals": ["review"],
            },
            {
                "title": "Clean",
                "eligible_for_local_preparation": True,
                "score": 0.80,
                "asset_count": 4,
                "risk_signals": [],
            },
        ])
        self.assertEqual(selected["title"], "Clean")

    def test_asset_work_prepares_product_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outputs = root / "outputs"
            outputs.mkdir()
            (outputs / "asset_income_runway.json").write_text(
                """{
                  "candidates": [{
                    "candidate_id": "asset_income_test",
                    "title": "ConstructiveRT browser extension package",
                    "theme": "constructivert_browser_extension",
                    "eligible_for_local_preparation": true,
                    "score": 0.9,
                    "asset_count": 1,
                    "risk_signals": [],
                    "public_benefit_signals": ["resource_efficiency"],
                    "revenue_paths": ["product_sale"],
                    "representative_assets": [{
                      "name": "ConstructiveRT_Chrome_v0_1_14.zip",
                      "kind": "file",
                      "path": "C:\\\\ConstructiveRT\\\\ConstructiveRT_Chrome_v0_1_14.zip"
                    }],
                    "local_next_steps": ["Create a product brief."]
                  }]
                }""",
                encoding="utf-8",
            )
            decision = AssetWorkRunner(root, {}).run()
            self.assertEqual(decision["status"], "local_asset_work_package_prepared")
            self.assertTrue((outputs / "asset_work" / "asset_income_test" / "product_brief.md").exists())
            self.assertTrue((outputs / "approval_requests" / "latest.json").exists())


if __name__ == "__main__":
    unittest.main()
