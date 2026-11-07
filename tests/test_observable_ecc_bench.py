import json
import tempfile
import unittest
from pathlib import Path

from tools.observable_ecc_bench import benchmark_curve, benchmark_qday_file, toy_curve_97, validate_paper_v02_rows
from tools.observable_ecc_bench.curve import mul, orbit, transition_ledgers


class ObservableEccBenchTests(unittest.TestCase):
    def test_paper_v02_transition_rows_match(self):
        curve = toy_curve_97()
        ledgers = transition_ledgers(curve, orbit(curve))

        ok, diffs = validate_paper_v02_rows(ledgers)

        self.assertTrue(ok, diffs)

    def test_ratio_ledger_refines_projected_schema(self):
        curve = toy_curve_97()
        ledgers = transition_ledgers(curve, orbit(curve))

        projected_ops = {ledgers[phase].op for phase in range(2, 10)}
        ratio_rows = {
            (
                ledgers[phase].D,
                ledgers[phase].U,
                ledgers[phase].V,
                ledgers[phase].m,
                ledgers[phase].lambda_value,
                ledgers[phase].ell,
                ledgers[phase].L,
                ledgers[phase].omega,
            )
            for phase in range(2, 10)
        }

        self.assertEqual(projected_ops, {"+G"})
        self.assertGreater(len(ratio_rows), 1)
        self.assertEqual(ledgers[1].D, ledgers[7].D)
        self.assertEqual(ledgers[1].V, ledgers[7].V)
        self.assertNotEqual(ledgers[1].paper_row(), ledgers[7].paper_row())

    def test_observable_support_law_tracks_x_fold(self):
        result = benchmark_curve()
        metrics = {metric.name: metric for metric in result.observables}

        self.assertEqual(metrics["point"].effective_support, result.order)
        self.assertEqual(metrics["compressed_point"].effective_support, result.order)
        self.assertLess(metrics["x"].effective_support, metrics["point"].effective_support)
        self.assertGreaterEqual(metrics["x"].max_fiber_size, 2)

    def test_recurrence_laws_hold_on_non_boundary_phases(self):
        result = benchmark_curve()

        self.assertEqual(result.recurrence_checks.doubling_failures, 0)
        self.assertEqual(result.recurrence_checks.generator_recurrence_failures, 0)
        self.assertIn(0, result.recurrence_checks.boundary_phases)

    def test_safety_scope_blocks_live_target_interpretation(self):
        result = benchmark_curve()

        self.assertIn("Local toy finite-curve analysis only", result.safety_scope)
        self.assertIn("no wallet/key recovery", result.safety_scope)
        self.assertIn("no network access", result.safety_scope)

    def test_qday_mode_validates_and_benchmarks_local_json(self):
        curve = toy_curve_97()
        private_key = 12
        public_key = list(mul(curve, private_key))
        payload = [
            {
                "bit_length": 17,
                "prime": curve.p,
                "curve_order": 79,
                "subgroup_order": 79,
                "cofactor": 1,
                "generator_point": list(curve.generator),
                "private_key": private_key,
                "public_key": public_key,
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "curves_qday.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            suite = benchmark_qday_file(path, bit_min=17, bit_max=17, exhaustive_under=100)

        self.assertEqual(suite.curves_total, 1)
        self.assertEqual(suite.curves_valid, 1)
        self.assertEqual(suite.results[0].mode, "exhaustive")
        self.assertTrue(suite.results[0].full_order_verified_by_enumeration)
        self.assertIn("no wallet/key recovery", suite.safety_scope)

    def test_qday_random_sampling_uses_non_prefix_phases(self):
        curve = toy_curve_97()
        private_key = 12
        public_key = list(mul(curve, private_key))
        payload = [
            {
                "bit_length": 20,
                "prime": curve.p,
                "curve_order": 79,
                "subgroup_order": 79,
                "cofactor": 1,
                "generator_point": list(curve.generator),
                "private_key": private_key,
                "public_key": public_key,
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "curves_qday.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            suite = benchmark_qday_file(
                path,
                bit_min=20,
                bit_max=20,
                sample_size=8,
                exhaustive_under=10,
                sample_strategy="random",
                sample_seed=1234,
            )

        result = suite.results[0]
        self.assertEqual(result.mode, "random_sample")
        self.assertEqual(result.phases_measured, 8)
        self.assertEqual(result.sample_strategy, "random")
        self.assertNotEqual(result.sampled_phase_preview, list(range(8)))


if __name__ == "__main__":
    unittest.main()
