"""secp256k1-size observable and synthetic paired-shell grid.

Safe scope:
- Local finite-sample analysis only.
- Local synthetic known-lane shell benchmarks only.
- No live targets, no puzzle solving, no wallet/key recovery, no browser or
  process tracing, and no network access.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

try:
    from tools.observable_ecc_bench.bench import ObservableMetric
    from tools.observable_ecc_bench.qday import (
        benchmark_qday_row,
        curve_benchmarkable,
        curve_from_qday_row,
        load_qday_rows,
        metric_lookup,
    )
    from tools.synthetic_paired_shell_runner import SyntheticShellConfig, run_curve
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from observable_ecc_bench.bench import ObservableMetric
    from observable_ecc_bench.qday import benchmark_qday_row, curve_benchmarkable, curve_from_qday_row, load_qday_rows, metric_lookup
    from synthetic_paired_shell_runner import SyntheticShellConfig, run_curve


DEFAULT_OUTDIR = Path("outputs/work_packages/secp256k1_grid_2026-06-25")
PAIR_COLLISION_ALPHA = 0.05


@dataclass(frozen=True)
class ObservableGridRow:
    sample_size: int
    seed: int
    mode: str
    phases: int
    keypair_matches: bool
    x_effective_support: float
    x_max_fiber: int
    x_colliding_pairs: int
    ratio_effective_support: float
    ratio_max_fiber: int
    ratio_colliding_pairs: int
    ratio_pair_collision_upper95: float
    small_x_effective_support: float
    small_x_max_fiber: int


@dataclass(frozen=True)
class SyntheticGridRow:
    hbits: int
    w_power: int
    mtop_bits: int
    seed: int
    trials: int
    q_candidates: float
    paired_candidates: float
    reduction: float
    q_false: float
    paired_false: float
    q_collisions: int
    paired_collisions: int
    q_found_rate: float
    paired_found_rate: float


@dataclass(frozen=True)
class SyntheticGridAggregate:
    hbits: int
    w_power: int
    mtop_bits: int
    seeds: int
    mean_reduction: float
    min_reduction: float
    max_reduction: float
    mean_q_candidates: float
    mean_paired_candidates: float
    mean_q_false: float
    mean_paired_false: float
    mean_q_collisions: float
    mean_paired_collisions: float


@dataclass(frozen=True)
class Secp256k1GridResult:
    source_json: str
    safety_scope: str
    bit_length: int
    observable_rows: list[ObservableGridRow]
    synthetic_rows: list[SyntheticGridRow]
    synthetic_aggregates: list[SyntheticGridAggregate]

    def to_dict(self) -> dict[str, object]:
        return {
            "source_json": self.source_json,
            "safety_scope": self.safety_scope,
            "bit_length": self.bit_length,
            "observable_rows": [asdict(row) for row in self.observable_rows],
            "synthetic_rows": [asdict(row) for row in self.synthetic_rows],
            "synthetic_aggregates": [asdict(row) for row in self.synthetic_aggregates],
        }


def parse_int_list(value: str) -> list[int]:
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def colliding_pairs(metric: ObservableMetric) -> int:
    size_sum = round(metric.collision_mass * metric.phases * metric.phases)
    return max(0, (size_sum - metric.phases) // 2)


def pair_collision_upper95(phases: int, observed_colliding_pairs: int) -> float:
    pair_count = phases * (phases - 1) // 2
    if pair_count <= 0:
        return 1.0
    if observed_colliding_pairs == 0:
        return -math.log(PAIR_COLLISION_ALPHA) / pair_count
    # Conservative normal-free estimate for a pair-collision probability.
    return min(1.0, (observed_colliding_pairs + 3.0) / pair_count)


def qday_row_256(qday_json: Path) -> dict[str, Any]:
    rows = load_qday_rows(qday_json, 256, 256)
    if len(rows) != 1:
        raise ValueError(f"expected one 256-bit row in {qday_json}, found {len(rows)}")
    return rows[0]


def run_observable_grid(
    qday_json: Path,
    sample_sizes: list[int],
    seeds: list[int],
) -> list[ObservableGridRow]:
    row = qday_row_256(qday_json)
    out: list[ObservableGridRow] = []
    for sample_size in sample_sizes:
        for seed in seeds:
            result = benchmark_qday_row(
                row,
                sample_size=sample_size,
                exhaustive_under=0,
                epsilon=0.125,
                sample_strategy="random",
                sample_seed=seed,
            )
            if not curve_benchmarkable(result.validation):
                raise ValueError("256-bit curve row is not benchmarkable")
            metrics = metric_lookup(result.observables)
            x_metric = metrics["x"]
            ratio_metric = metrics["ratio_ledger"]
            small_metric = metrics["small_x_category"]
            ratio_pairs = colliding_pairs(ratio_metric)
            out.append(
                ObservableGridRow(
                    sample_size=sample_size,
                    seed=seed,
                    mode=result.mode,
                    phases=result.phases_measured,
                    keypair_matches=result.validation.private_key_maps_to_public_key,
                    x_effective_support=x_metric.effective_support,
                    x_max_fiber=x_metric.max_fiber_size,
                    x_colliding_pairs=colliding_pairs(x_metric),
                    ratio_effective_support=ratio_metric.effective_support,
                    ratio_max_fiber=ratio_metric.max_fiber_size,
                    ratio_colliding_pairs=ratio_pairs,
                    ratio_pair_collision_upper95=pair_collision_upper95(result.phases_measured, ratio_pairs),
                    small_x_effective_support=small_metric.effective_support,
                    small_x_max_fiber=small_metric.max_fiber_size,
                )
            )
    return out


def run_synthetic_grid(
    qday_json: Path,
    seeds: list[int],
    hbits_values: list[int],
    w_power_values: list[int],
    mtop_bits_values: list[int],
    trials: int,
    m_power: int,
    t_power: int,
) -> tuple[list[SyntheticGridRow], list[SyntheticGridAggregate]]:
    row = qday_row_256(qday_json)
    bit_length, curve, _private_key, _public_key, subgroup_order, _curve_order, _cofactor = curve_from_qday_row(row)

    rows: list[SyntheticGridRow] = []
    for hbits in hbits_values:
        for w_power in w_power_values:
            for mtop_bits in mtop_bits_values:
                for seed in seeds:
                    config = SyntheticShellConfig(
                        bit_min=bit_length,
                        bit_max=bit_length,
                        trials=trials,
                        m_power=m_power,
                        t_power=t_power,
                        w_power=w_power,
                        hbits=hbits,
                        mtop_bits=mtop_bits,
                        seed=seed,
                    )
                    result = run_curve(curve, subgroup_order, bit_length, config)
                    qrow, prow = result.rows
                    rows.append(
                        SyntheticGridRow(
                            hbits=hbits,
                            w_power=w_power,
                            mtop_bits=mtop_bits,
                            seed=seed,
                            trials=trials,
                            q_candidates=qrow.avg_candidates,
                            paired_candidates=prow.avg_candidates,
                            reduction=result.candidate_reduction_factor,
                            q_false=qrow.avg_false_candidates,
                            paired_false=prow.avg_false_candidates,
                            q_collisions=qrow.dict_collisions,
                            paired_collisions=prow.dict_collisions,
                            q_found_rate=qrow.found_rate,
                            paired_found_rate=prow.found_rate,
                        )
                    )

    aggregates: list[SyntheticGridAggregate] = []
    for hbits in hbits_values:
        for w_power in w_power_values:
            for mtop_bits in mtop_bits_values:
                subset = [
                    row
                    for row in rows
                    if row.hbits == hbits and row.w_power == w_power and row.mtop_bits == mtop_bits
                ]
                reductions = [row.reduction for row in subset]
                aggregates.append(
                    SyntheticGridAggregate(
                        hbits=hbits,
                        w_power=w_power,
                        mtop_bits=mtop_bits,
                        seeds=len(subset),
                        mean_reduction=mean(reductions),
                        min_reduction=min(reductions),
                        max_reduction=max(reductions),
                        mean_q_candidates=mean(row.q_candidates for row in subset),
                        mean_paired_candidates=mean(row.paired_candidates for row in subset),
                        mean_q_false=mean(row.q_false for row in subset),
                        mean_paired_false=mean(row.paired_false for row in subset),
                        mean_q_collisions=mean(row.q_collisions for row in subset),
                        mean_paired_collisions=mean(row.paired_collisions for row in subset),
                    )
                )
    return rows, aggregates


def run_grid(
    qday_json: Path,
    sample_sizes: list[int],
    observable_seeds: list[int],
    synthetic_seeds: list[int],
    hbits_values: list[int],
    w_power_values: list[int],
    mtop_bits_values: list[int],
    trials: int,
    m_power: int,
    t_power: int,
) -> Secp256k1GridResult:
    observable_rows = run_observable_grid(qday_json, sample_sizes, observable_seeds)
    synthetic_rows, synthetic_aggregates = run_synthetic_grid(
        qday_json=qday_json,
        seeds=synthetic_seeds,
        hbits_values=hbits_values,
        w_power_values=w_power_values,
        mtop_bits_values=mtop_bits_values,
        trials=trials,
        m_power=m_power,
        t_power=t_power,
    )
    return Secp256k1GridResult(
        source_json=str(qday_json),
        safety_scope=(
            "Local secp256k1-size finite-sample and synthetic known-lane grid only; "
            "no live targets, no puzzle solving, no wallet/key recovery, no browser/process tracing, no network access."
        ),
        bit_length=256,
        observable_rows=observable_rows,
        synthetic_rows=synthetic_rows,
        synthetic_aggregates=synthetic_aggregates,
    )


def generate_markdown(result: Secp256k1GridResult) -> str:
    lines: list[str] = []
    lines.append("# secp256k1 Grid Report")
    lines.append("")
    lines.append(f"Source JSON: `{result.source_json}`")
    lines.append("")
    lines.append(f"Safety scope: {result.safety_scope}")
    lines.append("")
    lines.append("## Observable Sampling")
    lines.append("")
    lines.append(
        "| Sample | Seed | Keypair | x N_eff | x Coll Pairs | Ratio N_eff | Ratio Coll Pairs | Ratio Pair Upper95 |"
    )
    lines.append("|---:|---:|---|---:|---:|---:|---:|---:|")
    for row in result.observable_rows:
        lines.append(
            f"| {row.sample_size} | {row.seed} | {row.keypair_matches} | "
            f"{row.x_effective_support:.6g} | {row.x_colliding_pairs} | "
            f"{row.ratio_effective_support:.6g} | {row.ratio_colliding_pairs} | "
            f"{row.ratio_pair_collision_upper95:.6g} |"
        )
    lines.append("")
    lines.append("## Synthetic Paired-Shell Grid")
    lines.append("")
    lines.append(
        "| Hbits | W | Mtop | Seeds | Mean Reduction | Min | Max | Q Cand | Paired Cand | Q False | Paired False |"
    )
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in result.synthetic_aggregates:
        lines.append(
            f"| {row.hbits} | {row.w_power} | {row.mtop_bits} | {row.seeds} | "
            f"{row.mean_reduction:.6g} | {row.min_reduction:.6g} | {row.max_reduction:.6g} | "
            f"{row.mean_q_candidates:.6g} | {row.mean_paired_candidates:.6g} | "
            f"{row.mean_q_false:.6g} | {row.mean_paired_false:.6g} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The observable rows report finite random samples only. When ratio-ledger collisions are zero, "
        "the upper95 column gives a simple 95% upper bound on sampled pair-collision probability, "
        "computed as -ln(0.05) / choose(sample_size, 2)."
    )
    lines.append("")
    lines.append(
        "The synthetic rows use known generated lanes and secrets. They measure candidate-fiber refinement "
        "from q-only shells to paired q+r shells; they do not recover live keys."
    )
    lines.append("")
    return "\n".join(lines)


def write_outputs(result: Secp256k1GridResult, outdir: Path) -> dict[str, str]:
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / "secp256k1_grid_summary.json"
    md_path = outdir / "secp256k1_grid_summary.md"
    obs_csv = outdir / "secp256k1_observable_grid.csv"
    synth_csv = outdir / "secp256k1_synthetic_grid.csv"
    agg_csv = outdir / "secp256k1_synthetic_grid_aggregates.csv"

    json_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(generate_markdown(result), encoding="utf-8")

    with obs_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(result.observable_rows[0]).keys()))
        writer.writeheader()
        for row in result.observable_rows:
            writer.writerow(asdict(row))

    with synth_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(result.synthetic_rows[0]).keys()))
        writer.writeheader()
        for row in result.synthetic_rows:
            writer.writerow(asdict(row))

    with agg_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(result.synthetic_aggregates[0]).keys()))
        writer.writeheader()
        for row in result.synthetic_aggregates:
            writer.writerow(asdict(row))

    return {
        "json": str(json_path),
        "markdown": str(md_path),
        "observable_csv": str(obs_csv),
        "synthetic_csv": str(synth_csv),
        "aggregate_csv": str(agg_csv),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run secp256k1-size observable and synthetic shell grids.")
    parser.add_argument("--qday-json", required=True)
    parser.add_argument("--sample-sizes", default="1024,4096")
    parser.add_argument("--observable-seeds", default="20260625,20260626")
    parser.add_argument("--synthetic-seeds", default="20260625,20260626,20260627")
    parser.add_argument("--hbits", default="1,2")
    parser.add_argument("--w-powers", default="6,7")
    parser.add_argument("--mtop-bits", default="0,4")
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--m-power", type=int, default=4)
    parser.add_argument("--t-power", type=int, default=8)
    parser.add_argument("--outdir", default=str(DEFAULT_OUTDIR))
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    result = run_grid(
        qday_json=Path(args.qday_json),
        sample_sizes=parse_int_list(args.sample_sizes),
        observable_seeds=parse_int_list(args.observable_seeds),
        synthetic_seeds=parse_int_list(args.synthetic_seeds),
        hbits_values=parse_int_list(args.hbits),
        w_power_values=parse_int_list(args.w_powers),
        mtop_bits_values=parse_int_list(args.mtop_bits),
        trials=args.trials,
        m_power=args.m_power,
        t_power=args.t_power,
    )
    paths = write_outputs(result, Path(args.outdir))
    print("secp256k1 grid complete.")
    print(f"Observable rows: {len(result.observable_rows)}")
    print(f"Synthetic rows: {len(result.synthetic_rows)}")
    print(f"Markdown: {paths['markdown']}")
    print(f"JSON: {paths['json']}")


if __name__ == "__main__":
    main()
