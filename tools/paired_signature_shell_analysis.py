"""Analyze paired-signature shell locator summaries.

Safe scope:
- Reads local summary CSVs and source text only.
- Does not solve BTC puzzles.
- Does not recover private keys.
- Does not inspect wallets, browsers, processes, or networks.
- Does not perform external actions.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_OUTDIR = Path("outputs/work_packages/paired_signature_shell_locator_2026-06-25")


@dataclass(frozen=True)
class SummaryRow:
    mode: str
    R_power: int
    M_power: int
    T_power: int
    W_power: int
    Hbits: int
    targets: int
    found_rate: float
    avg_key_hits: float
    avg_candidates: float
    avg_false_candidates: float
    avg_trial_seconds: float
    dict_keys: int
    dict_collisions: int
    dict_seconds: float
    probe_cost_est: int


@dataclass(frozen=True)
class SourceReview:
    path: str
    bytes: int
    supports_conditional_synth: bool
    supports_qonly_mode: bool
    uses_secp256k1_constants: bool
    uses_puzzle_signature_constants: bool
    safety_note: str


@dataclass(frozen=True)
class Comparison:
    qonly_candidates_per_target: float
    paired_candidates_per_target: float
    qonly_false_candidates_per_target: float
    paired_false_candidates_per_target: float
    candidate_reduction_factor: float
    false_candidate_reduction: float
    qonly_dict_collisions: int
    paired_dict_collisions: int
    qonly_probe_cost_matches: bool
    paired_probe_cost_matches: bool
    paired_summary_consistent: bool
    qonly_summary_consistent: bool


@dataclass(frozen=True)
class AnalysisResult:
    safety_scope: str
    qonly_path: str
    paired_path: str
    source_review: SourceReview
    qonly: SummaryRow
    paired: SummaryRow
    comparison: Comparison

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def parse_float(value: str) -> float:
    return float(value.strip())


def parse_int(value: str) -> int:
    return int(value.strip())


def load_summary(path: Path, fallback_mode: str) -> SummaryRow:
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    if len(rows) != 1:
        raise ValueError(f"expected exactly one row in {path}, found {len(rows)}")
    row = rows[0]
    mode = row.get("mode") or fallback_mode
    return SummaryRow(
        mode=mode,
        R_power=parse_int(row["R_power"]),
        M_power=parse_int(row["M_power"]),
        T_power=parse_int(row["T_power"]),
        W_power=parse_int(row["W_power"]),
        Hbits=parse_int(row["Hbits"]),
        targets=parse_int(row["targets"]),
        found_rate=parse_float(row["found_rate"]),
        avg_key_hits=parse_float(row["avg_key_hits"]),
        avg_candidates=parse_float(row["avg_candidates"]),
        avg_false_candidates=parse_float(row["avg_false_candidates"]),
        avg_trial_seconds=parse_float(row["avg_trial_seconds"]),
        dict_keys=parse_int(row["dict_keys"]),
        dict_collisions=parse_int(row["dict_collisions"]),
        dict_seconds=parse_float(row["dict_seconds"]),
        probe_cost_est=parse_int(row["probe_cost_est"]),
    )


def expected_probe_cost(row: SummaryRow) -> int:
    window = 1 << row.W_power
    target_span = 1 << row.T_power
    blocks = (target_span + window - 1) // window + 1
    return window + blocks


def summary_consistent(row: SummaryRow) -> bool:
    expected_false = row.avg_candidates - row.found_rate
    return (
        row.T_power == row.R_power - row.M_power
        and row.probe_cost_est == expected_probe_cost(row)
        and math.isclose(row.avg_false_candidates, expected_false, rel_tol=1e-9, abs_tol=1e-6)
        and row.dict_keys + row.dict_collisions == (1 << row.W_power)
    )


def review_source(path: Path) -> SourceReview:
    text = path.read_text(encoding="utf-8", errors="replace")
    return SourceReview(
        path=str(path),
        bytes=len(text.encode("utf-8")),
        supports_conditional_synth='mode=="conditional_synth"' in text or "mode=conditional_synth" in text,
        supports_qonly_mode="qonly" in text.lower(),
        uses_secp256k1_constants="NID_secp256k1" in text and "GX_HEX" in text and "GY_HEX" in text,
        uses_puzzle_signature_constants="PUZZLE_R_HEX" in text and "PUZZLE_S_HEX" in text and "PUZZLE_Z_HEX" in text,
        safety_note=(
            "Source appears to expose conditional synthetic testing only in this file. "
            "Do not convert it into a live key-recovery or wallet-targeting runner."
        ),
    )


def compare(qonly: SummaryRow, paired: SummaryRow) -> Comparison:
    if paired.avg_candidates == 0:
        reduction = math.inf
    else:
        reduction = qonly.avg_candidates / paired.avg_candidates
    false_reduction = qonly.avg_false_candidates - paired.avg_false_candidates
    return Comparison(
        qonly_candidates_per_target=qonly.avg_candidates,
        paired_candidates_per_target=paired.avg_candidates,
        qonly_false_candidates_per_target=qonly.avg_false_candidates,
        paired_false_candidates_per_target=paired.avg_false_candidates,
        candidate_reduction_factor=reduction,
        false_candidate_reduction=false_reduction,
        qonly_dict_collisions=qonly.dict_collisions,
        paired_dict_collisions=paired.dict_collisions,
        qonly_probe_cost_matches=qonly.probe_cost_est == expected_probe_cost(qonly),
        paired_probe_cost_matches=paired.probe_cost_est == expected_probe_cost(paired),
        paired_summary_consistent=summary_consistent(paired),
        qonly_summary_consistent=summary_consistent(qonly),
    )


def analyze(qonly_path: Path, paired_path: Path, source_path: Path) -> AnalysisResult:
    qonly = load_summary(qonly_path, fallback_mode="qonly")
    paired = load_summary(paired_path, fallback_mode="conditional_synth")
    return AnalysisResult(
        safety_scope=(
            "Local summary/source analysis only; no live targets, no puzzle solving, "
            "no wallet/key recovery, no browser/process tracing, no network access."
        ),
        qonly_path=str(qonly_path),
        paired_path=str(paired_path),
        source_review=review_source(source_path),
        qonly=qonly,
        paired=paired,
        comparison=compare(qonly, paired),
    )


def generate_markdown(result: AnalysisResult) -> str:
    q = result.qonly
    p = result.paired
    c = result.comparison
    s = result.source_review
    lines: list[str] = []
    lines.append("# Paired Signature Shell Locator Analysis")
    lines.append("")
    lines.append(f"Safety scope: {result.safety_scope}")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- Q-only summary: `{result.qonly_path}`")
    lines.append(f"- Paired summary: `{result.paired_path}`")
    lines.append(f"- Source reviewed: `{s.path}`")
    lines.append("")
    lines.append("## Source Review")
    lines.append("")
    lines.append(f"- Uses secp256k1 constants: `{s.uses_secp256k1_constants}`")
    lines.append(f"- Uses puzzle signature constants: `{s.uses_puzzle_signature_constants}`")
    lines.append(f"- Supports `conditional_synth`: `{s.supports_conditional_synth}`")
    lines.append(f"- Supports q-only mode in this file: `{s.supports_qonly_mode}`")
    lines.append(f"- Note: {s.safety_note}")
    lines.append("")
    lines.append("## Summary Comparison")
    lines.append("")
    lines.append("| Metric | Q-only | Paired conditional |")
    lines.append("|---|---:|---:|")
    lines.append(f"| Targets | {q.targets} | {p.targets} |")
    lines.append(f"| Found rate | {q.found_rate:.6f} | {p.found_rate:.6f} |")
    lines.append(f"| Avg candidates | {q.avg_candidates:.6f} | {p.avg_candidates:.6f} |")
    lines.append(f"| Avg false candidates | {q.avg_false_candidates:.6f} | {p.avg_false_candidates:.6f} |")
    lines.append(f"| Dict keys | {q.dict_keys} | {p.dict_keys} |")
    lines.append(f"| Dict collisions | {q.dict_collisions} | {p.dict_collisions} |")
    lines.append(f"| Avg trial seconds | {q.avg_trial_seconds:.6f} | {p.avg_trial_seconds:.6f} |")
    lines.append(f"| Probe cost estimate | {q.probe_cost_est} | {p.probe_cost_est} |")
    lines.append("")
    lines.append("## Checks")
    lines.append("")
    lines.append(f"- Q-only probe cost matches `2^W + ceil(2^T / 2^W) + 1`: `{c.qonly_probe_cost_matches}`")
    lines.append(f"- Paired probe cost matches `2^W + ceil(2^T / 2^W) + 1`: `{c.paired_probe_cost_matches}`")
    lines.append(f"- Q-only summary internally consistent: `{c.qonly_summary_consistent}`")
    lines.append(f"- Paired summary internally consistent: `{c.paired_summary_consistent}`")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        f"The paired conditional observable reduced average candidates from "
        f"{c.qonly_candidates_per_target:.2f} to {c.paired_candidates_per_target:.2f}, "
        f"a {c.candidate_reduction_factor:.2f}x reduction on these four synthetic targets."
    )
    lines.append("")
    lines.append(
        f"False candidates dropped from {c.qonly_false_candidates_per_target:.2f} per target "
        f"to {c.paired_false_candidates_per_target:.2f}. Dictionary collisions also dropped "
        f"from {c.qonly_dict_collisions} to {c.paired_dict_collisions}."
    )
    lines.append("")
    lines.append(
        "This supports the observable-indexed claim in a narrow synthetic setting: pairing the Q-lane "
        "shell with the signature-derived R-lane shell can refine the candidate fiber that remains under "
        "Q-only shell conditioning."
    )
    lines.append("")
    lines.append(
        "It does not prove live private-key recovery. The paired run is `conditional_synth`, meaning the "
        "synthetic lane value is supplied. The result should be treated as a local phase/fiber refinement "
        "test, not as a deployed attack."
    )
    lines.append("")
    return "\n".join(lines)


def write_outputs(result: AnalysisResult, outdir: Path) -> dict[str, str]:
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / "paired_signature_shell_analysis.json"
    md_path = outdir / "paired_signature_shell_analysis.md"
    json_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(generate_markdown(result), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze local paired shell locator summary files.")
    parser.add_argument("--qonly-summary", required=True)
    parser.add_argument("--paired-summary", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--outdir", default=str(DEFAULT_OUTDIR))
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    result = analyze(Path(args.qonly_summary), Path(args.paired_summary), Path(args.source))
    paths = write_outputs(result, Path(args.outdir))
    print("Paired signature shell analysis complete.")
    print(f"Q-only consistent: {result.comparison.qonly_summary_consistent}")
    print(f"Paired consistent: {result.comparison.paired_summary_consistent}")
    print(f"Candidate reduction factor: {result.comparison.candidate_reduction_factor:.6f}")
    print(f"Markdown: {paths['markdown']}")
    print(f"JSON: {paths['json']}")


if __name__ == "__main__":
    main()
