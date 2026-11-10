import csv
import tempfile
import unittest
from pathlib import Path

from tools.paired_signature_shell_analysis import analyze, expected_probe_cost, load_summary


class PairedSignatureShellAnalysisTests(unittest.TestCase):
    def test_expected_probe_cost_matches_supplied_parameters(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "R_power",
                        "M_power",
                        "T_power",
                        "W_power",
                        "Hbits",
                        "targets",
                        "found_rate",
                        "avg_key_hits",
                        "avg_candidates",
                        "avg_false_candidates",
                        "avg_trial_seconds",
                        "dict_keys",
                        "dict_collisions",
                        "dict_seconds",
                        "probe_cost_est",
                    ]
                )
                writer.writerow([135, 103, 32, 16, 4, 4, 1, 10.75, 10.75, 9.75, 0.1, 65529, 7, 1.0, 131073])

            row = load_summary(path, fallback_mode="qonly")

        self.assertEqual(expected_probe_cost(row), 131073)

    def test_analysis_compares_qonly_and_paired_summaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            qonly = root / "qonly.csv"
            paired = root / "paired.csv"
            source = root / "locator.cpp"
            qonly.write_text(
                "R_power,M_power,T_power,W_power,Hbits,targets,found_rate,avg_key_hits,avg_candidates,avg_false_candidates,avg_trial_seconds,dict_keys,dict_collisions,dict_seconds,probe_cost_est\n"
                "135,103,32,16,4,4,1.000000,10.750000,10.750000,9.750000,0.383928,65529,7,1.612460,131073\n",
                encoding="utf-8",
            )
            paired.write_text(
                "mode,R_power,M_power,T_power,W_power,Hbits,targets,found_rate,avg_key_hits,avg_candidates,avg_false_candidates,avg_trial_seconds,dict_keys,dict_collisions,dict_seconds,probe_cost_est\n"
                "conditional_synth,135,103,32,16,4,4,1.000000,1.000000,1.000000,0.000000,0.734912,65536,0,3.201674,131073\n",
                encoding="utf-8",
            )
            source.write_text(
                'NID_secp256k1 GX_HEX GY_HEX PUZZLE_R_HEX PUZZLE_S_HEX PUZZLE_Z_HEX mode=="conditional_synth"',
                encoding="utf-8",
            )

            result = analyze(qonly, paired, source)

        self.assertTrue(result.comparison.qonly_summary_consistent)
        self.assertTrue(result.comparison.paired_summary_consistent)
        self.assertEqual(result.comparison.candidate_reduction_factor, 10.75)
        self.assertEqual(result.comparison.paired_false_candidates_per_target, 0.0)
        self.assertTrue(result.source_review.supports_conditional_synth)
        self.assertFalse(result.source_review.supports_qonly_mode)


if __name__ == "__main__":
    unittest.main()
