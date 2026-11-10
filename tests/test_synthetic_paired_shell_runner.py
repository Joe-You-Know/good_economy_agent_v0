import json
import tempfile
import unittest
from pathlib import Path

from tools.observable_ecc_bench import toy_curve_97
from tools.observable_ecc_bench.curve import mul
from tools.synthetic_paired_shell_runner import SyntheticShellConfig, run_suite


class SyntheticPairedShellRunnerTests(unittest.TestCase):
    def test_synthetic_runner_compares_qonly_and_paired_modes(self):
        curve = toy_curve_97()
        private_key = 12
        payload = [
            {
                "bit_length": 17,
                "prime": curve.p,
                "curve_order": 79,
                "subgroup_order": 79,
                "cofactor": 1,
                "generator_point": list(curve.generator),
                "private_key": private_key,
                "public_key": list(mul(curve, private_key)),
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            qday_json = Path(tmp) / "curves_qday.json"
            qday_json.write_text(json.dumps(payload), encoding="utf-8")
            suite = run_suite(
                qday_json,
                SyntheticShellConfig(
                    bit_min=17,
                    bit_max=17,
                    trials=5,
                    m_power=1,
                    t_power=4,
                    w_power=2,
                    hbits=1,
                    mtop_bits=0,
                    seed=123,
                ),
            )

        self.assertEqual(suite.curves_total, 1)
        self.assertEqual(len(suite.results[0].rows), 2)
        self.assertEqual({row.mode for row in suite.results[0].rows}, {"qonly", "paired_synth"})
        self.assertIn("no wallet/key recovery", suite.safety_scope)


if __name__ == "__main__":
    unittest.main()
