"""Self-contained tests suitable for offline GitHub CI (no external files or tokens)."""
import csv
import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from agent.buyer_precedent import load_evidence, evaluate_mandate


class BuyerPrecedentTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        source = b"100\tA\n" * 100
        (self.root / "source.tsv").write_bytes(source)
        (self.root / "source.tsv.gz").write_bytes(gzip.compress(source))
        (self.root / "source.crtc").write_bytes(b"TEST_PLACEHOLDER_CRCT")
        variants = {}
        for method, filename in [("explicit", "source.tsv"), ("gzip", "source.tsv.gz"), ("constructive", "source.crtc")]:
            content = (self.root / filename).read_bytes()
            variants[method] = {"name": filename, "artifact_bytes": len(content), "artifact_sha256": hashlib.sha256(content).hexdigest()}
        source_hash = hashlib.sha256(source).hexdigest()
        summary = {"all_exact_verified": True, "full_success": True, "transfers": 6,
                   "scope": "synthetic fixture, not a benchmark",
                   "source": {"source_bytes": len(source), "source_sha256": source_hash},
                   "candidate_manifest": {"source_bytes": len(source), "source_sha256": source_hash, "variants": variants},
                   "scenarios": [{"profile": {"name": "test-net"}, "rounds": 2,
                                   "median_wall_ms": {"explicit": 99, "gzip": 80, "constructive": 70}}]}
        self.summary = self.root / "summary.json"
        self.summary.write_text(json.dumps(summary))
        self.trials = self.root / "trials.csv"
        fields = ["scenario", "method", "exact_original_sha256_verified", "source_bytes", "artifact_bytes",
                  "total_wall_ms", "reconstruction_verified_ms"]
        with self.trials.open("w", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=fields)
            writer.writeheader()
            for method, time in [("explicit", 99), ("gzip", 80), ("constructive", 70)]:
                for i in range(2):
                    writer.writerow({"scenario": "test-net", "method": method,
                                     "exact_original_sha256_verified": "True", "source_bytes": len(source),
                                     "artifact_bytes": variants[method]["artifact_bytes"],
                                     "total_wall_ms": time, "reconstruction_verified_ms": 2})
        self.mandate = {"name": "test-mandate", "profile": "test-net", "transfers_per_month": 2000,
                        "egress_usd_per_gb": 0.09, "cpu_usd_per_hour": 0.03,
                        "monthly_spend_authority_usd": 10, "upfront_purchase_authority_usd": 10,\n                        "evaluation_horizon_months": 12, "max_verified_transfer_ms": 100,\n                        "opt_in_updates": False, "optional_update_subscription_usd_per_month": 0.99,
                        "one_time_purchase_prices_usd": {"explicit": 0, "gzip": 0, "constructive": 4.99}}

    def test_exact_artifact_check_and_no_real_revenue(self):
        evidence = load_evidence(self.summary, self.trials, self.root)
        self.assertTrue(evidence["artifact_checks"]["gzip_independent_roundtrip"])
        self.assertFalse(evidence["artifact_checks"]["constructive_independent_decode"])
        self.assertEqual(evidence["trial_count"], 6)
        decision = evaluate_mandate(evidence, self.mandate)
        self.assertEqual(decision["selected"], "gzip")
        self.assertFalse(decision["transaction_occurred"])
        self.assertEqual(decision["actual_revenue_usd"], 0)

    def test_selects_constructive_when_economically_valid(self):
        evidence = load_evidence(self.summary, self.trials, self.root)
        mandate = dict(self.mandate, one_time_purchase_prices_usd={"explicit": 0, "gzip": 0, "constructive": 0},
                       max_verified_transfer_ms=75)
        self.assertEqual(evaluate_mandate(evidence, mandate)["selected"], "constructive")


    def test_perpetual_price_not_recurring_and_updates_opt_in(self):
        evidence = load_evidence(self.summary, self.trials, self.root)
        mandate = dict(self.mandate, max_verified_transfer_ms=75)
        base = evaluate_mandate(evidence, mandate)
        option = next(x for x in base["candidates"] if x["method"] == "constructive")
        self.assertEqual(option["one_time_purchase_usd"], 4.99)
        self.assertAlmostEqual(option["monthly_amortized_purchase_usd"], 4.99 / 12, places=5)
        self.assertEqual(option["monthly_optional_updates_usd"], 0)
        self.assertTrue(option["perpetual_right_to_purchased_version"])
        updated = evaluate_mandate(evidence, dict(mandate, opt_in_updates=True))
        paid = next(x for x in updated["candidates"] if x["method"] == "constructive")
        self.assertEqual(paid["monthly_optional_updates_usd"], 0.99)
        self.assertAlmostEqual(paid["total_estimated_monthly_usd"] - option["total_estimated_monthly_usd"], 0.99)

    def test_purchased_version_remains_eligible_without_updates(self):
        evidence = load_evidence(self.summary, self.trials, self.root)
        mandate = dict(self.mandate, max_verified_transfer_ms=75,
                       monthly_spend_authority_usd=0, opt_in_updates=False)
        result = evaluate_mandate(evidence, mandate)
        option = next(x for x in result["candidates"] if x["method"] == "constructive")
        self.assertTrue(option["eligible"])
        self.assertTrue(option["perpetual_right_to_purchased_version"])

    def test_upfront_authority_independent_from_subscription(self):
        evidence = load_evidence(self.summary, self.trials, self.root)
        result = evaluate_mandate(evidence, dict(self.mandate, upfront_purchase_authority_usd=4))
        option = next(x for x in result["candidates"] if x["method"] == "constructive")
        self.assertIn("upfront_purchase_authority", option["disqualification"])

    def test_tampering_rejected(self):
        text = self.trials.read_text()
        self.trials.write_text(text.replace("True", "False", 1))
        with self.assertRaisesRegex(ValueError, "Non-verified transfer"):
            load_evidence(self.summary, self.trials, self.root)

    def test_corrupted_gzip_rejected(self):
        (self.root / "source.tsv.gz").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "Artifact does not match"):
            load_evidence(self.summary, self.trials, self.root)

    def test_negative_price_rejected(self):
        evidence = load_evidence(self.summary, self.trials, self.root)
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            evaluate_mandate(evidence, dict(self.mandate, cpu_usd_per_hour=-1))


if __name__ == "__main__":
    unittest.main()