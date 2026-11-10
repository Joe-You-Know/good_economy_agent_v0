"""Synthetic q-only vs paired shell benchmark.

Safe scope:
- Local synthetic secrets only.
- Local qday/toy curve parameters only.
- No live targets, no puzzle solving, no wallet/key recovery, no browser or
  process tracing, and no network access.

The benchmark tests a narrow observable-indexed claim: when a q-lane shell
leaves multiple candidate offsets, adding an independently generated
signature-affine r-lane shell can refine the candidate fiber.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    from tools.observable_ecc_bench.curve import Curve, Point, add, inv_mod, mul, negate
    from tools.observable_ecc_bench.qday import curve_from_qday_row, load_qday_rows
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from observable_ecc_bench.curve import Curve, Point, add, inv_mod, mul, negate
    from observable_ecc_bench.qday import curve_from_qday_row, load_qday_rows


DEFAULT_OUTDIR = Path("outputs/work_packages/synthetic_paired_shell_runner_2026-06-25")


Shell = tuple[int, int, int, int]
ShellPair = tuple[Shell, Shell]
PairedShellPair = tuple[Shell, Shell, Shell, Shell]


@dataclass(frozen=True)
class SyntheticShellConfig:
    bit_min: int
    bit_max: int
    trials: int
    m_power: int
    t_power: int
    w_power: int
    hbits: int
    mtop_bits: int
    seed: int


@dataclass(frozen=True)
class SyntheticShellRow:
    bit_length: int
    mode: str
    trials: int
    found_rate: float
    avg_key_hits: float
    avg_candidates: float
    avg_false_candidates: float
    dict_keys: int
    dict_collisions: int
    probe_cost_est: int
    notes: str


@dataclass(frozen=True)
class SyntheticShellCurveResult:
    bit_length: int
    curve_name: str
    subgroup_order: int
    rows: list[SyntheticShellRow]
    candidate_reduction_factor: float
    false_candidate_reduction: float


@dataclass(frozen=True)
class SyntheticShellSuite:
    source_json: str
    safety_scope: str
    config: SyntheticShellConfig
    curves_total: int
    results: list[SyntheticShellCurveResult]

    def to_dict(self) -> dict[str, object]:
        return {
            "source_json": self.source_json,
            "safety_scope": self.safety_scope,
            "config": asdict(self.config),
            "curves_total": self.curves_total,
            "results": [
                {
                    "bit_length": result.bit_length,
                    "curve_name": result.curve_name,
                    "subgroup_order": result.subgroup_order,
                    "rows": [asdict(row) for row in result.rows],
                    "candidate_reduction_factor": result.candidate_reduction_factor,
                    "false_candidate_reduction": result.false_candidate_reduction,
                }
                for result in self.results
            ],
        }


def top_fixed(value: int, bits: int, fixed: int) -> int:
    if bits <= 0:
        return 0
    if fixed > bits:
        value >>= fixed - bits
    elif fixed < bits:
        value <<= bits - fixed
    return value & ((1 << bits) - 1)


def top_norm(value: int, bits: int) -> int:
    if bits <= 0 or value == 0:
        return 0
    width = value.bit_length()
    if width > bits:
        value >>= width - bits
    elif width < bits:
        value <<= bits - width
    return value & ((1 << bits) - 1)


def bucket(a: int, b: int, radius: int = 31) -> int:
    delta = a - b
    if delta < -radius:
        delta = -radius
    if delta > radius:
        delta = radius
    return delta + radius


def point_x(point: Point) -> int:
    if point is None:
        return 0
    return point[0]


def shell_from_x(curve: Curve, x_value: int, step_point: Point, hbits: int, mtop_bits: int) -> Shell:
    sx = point_x(step_point)
    denominator = (sx - x_value) % curve.p
    if denominator == 0:
        denominator = 1
    inverse = inv_mod(denominator, curve.p)
    m_value = (denominator * inverse - 1) // curve.p
    return (
        top_fixed(m_value, mtop_bits, fixed=curve.p.bit_length()),
        bucket(denominator.bit_length(), inverse.bit_length()),
        top_norm(denominator, hbits),
        top_norm(inverse, hbits),
    )


def shell_pair_for_point(curve: Curve, point: Point, step_point: Point, hbits: int, mtop_bits: int) -> ShellPair:
    next_point = add(curve, point, step_point)
    return (
        shell_from_x(curve, point_x(point), step_point, hbits, mtop_bits),
        shell_from_x(curve, point_x(next_point), step_point, hbits, mtop_bits),
    )


def point_sub(curve: Curve, left: Point, right: Point) -> Point:
    return add(curve, left, negate(curve, right))


def build_dictionaries(
    curve: Curve,
    order: int,
    m_scalar: int,
    window: int,
    beta: int,
    hbits: int,
    mtop_bits: int,
) -> tuple[dict[ShellPair, list[int]], dict[PairedShellPair, list[int]], Point, Point, Point, Point]:
    step_q = mul(curve, m_scalar)
    block_q = mul(curve, (m_scalar * window) % order)
    step_r = mul(curve, (beta * m_scalar) % order)
    block_r = mul(curve, (beta * m_scalar * window) % order)
    qonly: dict[ShellPair, list[int]] = defaultdict(list)
    paired: dict[PairedShellPair, list[int]] = defaultdict(list)

    for offset in range(1, window + 1):
        q_point = mul(curve, (offset * m_scalar) % order)
        r_point = mul(curve, (beta * offset * m_scalar) % order)
        q_key = shell_pair_for_point(curve, q_point, step_q, hbits, mtop_bits)
        r_key = shell_pair_for_point(curve, r_point, step_r, hbits, mtop_bits)
        qonly[q_key].append(offset)
        paired[(q_key[0], q_key[1], r_key[0], r_key[1])].append(offset)

    return qonly, paired, step_q, block_q, step_r, block_r


def collision_count(dictionary: dict[Any, list[int]]) -> int:
    return sum(len(values) - 1 for values in dictionary.values() if len(values) > 1)


def run_mode_trials(
    curve: Curve,
    order: int,
    mode: str,
    dictionary: dict[Any, list[int]],
    m_scalar: int,
    window: int,
    target_span: int,
    alpha: int,
    beta: int,
    trials: int,
    rng: random.Random,
    hbits: int,
    mtop_bits: int,
) -> SyntheticShellRow:
    step_q = mul(curve, m_scalar % order)
    step_r = mul(curve, (beta * m_scalar) % order)
    found = 0
    total_hits = 0
    total_candidates = 0
    total_false = 0
    blocks = (target_span + window - 1) // window + 1

    for _ in range(trials):
        lane = rng.randrange(1, max(2, m_scalar))
        true_t = rng.randrange(1, target_span)
        secret = (lane + true_t * m_scalar) % order
        q_point = mul(curve, secret)
        alpha_g = mul(curve, alpha % order)
        beta_q = mul(curve, (beta * secret) % order)
        r_point = add(curve, alpha_g, beta_q)
        lane_q = point_sub(curve, q_point, mul(curve, lane % order))
        lane_r_remove = mul(curve, (alpha + beta * lane) % order)
        lane_r = point_sub(curve, r_point, lane_r_remove)

        trial_found = False
        for block in range(0, blocks * window, window):
            q_probe = point_sub(curve, lane_q, mul(curve, (block * m_scalar) % order))
            if q_probe is None:
                continue
            q_key = shell_pair_for_point(curve, q_probe, step_q, hbits, mtop_bits)
            if mode == "qonly":
                key = q_key
            else:
                r_probe = point_sub(curve, lane_r, mul(curve, (beta * block * m_scalar) % order))
                if r_probe is None:
                    continue
                r_key = shell_pair_for_point(curve, r_probe, step_r, hbits, mtop_bits)
                key = (q_key[0], q_key[1], r_key[0], r_key[1])

            offsets = dictionary.get(key)
            if not offsets:
                continue
            total_hits += 1
            for offset in offsets:
                candidate_t = block + offset
                if 1 <= candidate_t < target_span:
                    total_candidates += 1
                    if candidate_t == true_t:
                        trial_found = True
                    else:
                        total_false += 1
        if trial_found:
            found += 1

    return SyntheticShellRow(
        bit_length=int(curve.name.split("_")[1]) if curve.name.startswith("qday_") else 0,
        mode=mode,
        trials=trials,
        found_rate=found / trials,
        avg_key_hits=total_hits / trials,
        avg_candidates=total_candidates / trials,
        avg_false_candidates=total_false / trials,
        dict_keys=len(dictionary),
        dict_collisions=collision_count(dictionary),
        probe_cost_est=window + blocks,
        notes="synthetic known-lane benchmark; not live key recovery",
    )


def run_curve(
    curve: Curve,
    order: int,
    bit_length: int,
    config: SyntheticShellConfig,
) -> SyntheticShellCurveResult:
    m_scalar = 1 << config.m_power
    target_span = 1 << config.t_power
    window = 1 << config.w_power
    if m_scalar * target_span >= order:
        raise ValueError(
            f"synthetic range too large for bit {bit_length}: 2^M * 2^T >= order"
        )

    rng = random.Random(config.seed + bit_length * 7919)
    beta = 17 + bit_length * 2
    while math.gcd(beta, order) != 1:
        beta += 1
    alpha = 29 + bit_length
    qdict, pdict, *_ = build_dictionaries(
        curve=curve,
        order=order,
        m_scalar=m_scalar,
        window=window,
        beta=beta,
        hbits=config.hbits,
        mtop_bits=config.mtop_bits,
    )
    qrow = run_mode_trials(
        curve=curve,
        order=order,
        mode="qonly",
        dictionary=qdict,
        m_scalar=m_scalar,
        window=window,
        target_span=target_span,
        alpha=alpha,
        beta=beta,
        trials=config.trials,
        rng=random.Random(rng.randrange(1 << 60)),
        hbits=config.hbits,
        mtop_bits=config.mtop_bits,
    )
    prow = run_mode_trials(
        curve=curve,
        order=order,
        mode="paired_synth",
        dictionary=pdict,
        m_scalar=m_scalar,
        window=window,
        target_span=target_span,
        alpha=alpha,
        beta=beta,
        trials=config.trials,
        rng=random.Random(rng.randrange(1 << 60)),
        hbits=config.hbits,
        mtop_bits=config.mtop_bits,
    )
    reduction = math.inf if prow.avg_candidates == 0 else qrow.avg_candidates / prow.avg_candidates
    return SyntheticShellCurveResult(
        bit_length=bit_length,
        curve_name=curve.name,
        subgroup_order=order,
        rows=[qrow, prow],
        candidate_reduction_factor=reduction,
        false_candidate_reduction=qrow.avg_false_candidates - prow.avg_false_candidates,
    )


def run_suite(qday_json: Path, config: SyntheticShellConfig) -> SyntheticShellSuite:
    results: list[SyntheticShellCurveResult] = []
    for row in load_qday_rows(qday_json, config.bit_min, config.bit_max):
        bit_length, curve, _private_key, _public_key, subgroup_order, _curve_order, _cofactor = curve_from_qday_row(row)
        results.append(run_curve(curve, subgroup_order, bit_length, config))
    return SyntheticShellSuite(
        source_json=str(qday_json),
        safety_scope=(
            "Local synthetic known-secret benchmark only; no live targets, no puzzle solving, "
            "no wallet/key recovery, no browser/process tracing, no network access."
        ),
        config=config,
        curves_total=len(results),
        results=results,
    )


def generate_markdown(suite: SyntheticShellSuite) -> str:
    lines: list[str] = []
    cfg = suite.config
    lines.append("# Synthetic Paired Shell Runner Report")
    lines.append("")
    lines.append(f"Source JSON: `{suite.source_json}`")
    lines.append("")
    lines.append(f"Safety scope: {suite.safety_scope}")
    lines.append("")
    lines.append("## Config")
    lines.append("")
    lines.append(f"- Bit range: `{cfg.bit_min}-{cfg.bit_max}`")
    lines.append(f"- Trials per curve/mode: `{cfg.trials}`")
    lines.append(f"- M power: `{cfg.m_power}`")
    lines.append(f"- T power: `{cfg.t_power}`")
    lines.append(f"- W power: `{cfg.w_power}`")
    lines.append(f"- Hbits: `{cfg.hbits}`")
    lines.append(f"- M-top bits: `{cfg.mtop_bits}`")
    lines.append(f"- Seed: `{cfg.seed}`")
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("| Bits | Q Cand | P Cand | Reduction | Q False | P False | Q Coll | P Coll | Q Found | P Found |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for result in suite.results:
        qrow, prow = result.rows
        lines.append(
            f"| {result.bit_length} | {qrow.avg_candidates:.3f} | {prow.avg_candidates:.3f} | "
            f"{result.candidate_reduction_factor:.3f} | {qrow.avg_false_candidates:.3f} | "
            f"{prow.avg_false_candidates:.3f} | {qrow.dict_collisions} | {prow.dict_collisions} | "
            f"{qrow.found_rate:.3f} | {prow.found_rate:.3f} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "This benchmark uses known synthetic lanes and generated secrets. It measures candidate-fiber "
        "refinement when an independently generated r-lane shell is paired with the q-lane shell."
    )
    lines.append("")
    lines.append(
        "A reduction factor above 1 means the paired observable narrowed the candidate fiber relative "
        "to q-only shell conditioning for the same synthetic search geometry."
    )
    lines.append("")
    lines.append(
        "This does not recover live keys and does not validate passive capture or public-output-only inversion."
    )
    lines.append("")
    return "\n".join(lines)


def write_outputs(suite: SyntheticShellSuite, outdir: Path) -> dict[str, str]:
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / "synthetic_paired_shell_summary.json"
    md_path = outdir / "synthetic_paired_shell_summary.md"
    csv_path = outdir / "synthetic_paired_shell_summary.csv"
    json_path.write_text(json.dumps(suite.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(generate_markdown(suite), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "bit_length",
                "mode",
                "trials",
                "found_rate",
                "avg_key_hits",
                "avg_candidates",
                "avg_false_candidates",
                "dict_keys",
                "dict_collisions",
                "probe_cost_est",
                "notes",
            ],
        )
        writer.writeheader()
        for result in suite.results:
            for row in result.rows:
                writer.writerow(asdict(row))
    return {"json": str(json_path), "markdown": str(md_path), "csv": str(csv_path)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run synthetic q-only vs paired shell benchmark.")
    parser.add_argument("--qday-json", required=True)
    parser.add_argument("--bit-min", type=int, default=17)
    parser.add_argument("--bit-max", type=int, default=24)
    parser.add_argument("--trials", type=int, default=40)
    parser.add_argument("--m-power", type=int, default=4)
    parser.add_argument("--t-power", type=int, default=8)
    parser.add_argument("--w-power", type=int, default=6)
    parser.add_argument("--hbits", type=int, default=1)
    parser.add_argument("--mtop-bits", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260625)
    parser.add_argument("--outdir", default=str(DEFAULT_OUTDIR))
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config = SyntheticShellConfig(
        bit_min=args.bit_min,
        bit_max=args.bit_max,
        trials=args.trials,
        m_power=args.m_power,
        t_power=args.t_power,
        w_power=args.w_power,
        hbits=args.hbits,
        mtop_bits=args.mtop_bits,
        seed=args.seed,
    )
    suite = run_suite(Path(args.qday_json), config)
    paths = write_outputs(suite, Path(args.outdir))
    print("Synthetic paired shell benchmark complete.")
    print(f"Curves: {suite.curves_total}")
    print(f"Markdown: {paths['markdown']}")
    print(f"JSON: {paths['json']}")
    print(f"CSV: {paths['csv']}")


if __name__ == "__main__":
    main()
