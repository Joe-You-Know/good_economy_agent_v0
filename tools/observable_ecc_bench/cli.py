from __future__ import annotations

import argparse
from pathlib import Path

from .bench import benchmark_curve, write_outputs
from .qday import benchmark_qday_file, write_qday_outputs


DEFAULT_OUTDIR = Path("outputs/work_packages/observable_ecc_bench_2026-06-19")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local observable-indexed ECC benchmark on the v0.2 toy curve."
    )
    parser.add_argument(
        "--outdir",
        default=str(DEFAULT_OUTDIR),
        help="Output directory for JSON, CSV, and Markdown summaries.",
    )
    parser.add_argument(
        "--epsilon",
        type=float,
        default=0.125,
        help="Small-x threshold as a fraction of p.",
    )
    parser.add_argument(
        "--qday-json",
        default=None,
        help="Optional curves_qday.json path. When set, runs qday multi-curve mode.",
    )
    parser.add_argument("--bit-min", type=int, default=17, help="Minimum qday bit length.")
    parser.add_argument("--bit-max", type=int, default=28, help="Maximum qday bit length.")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=4096,
        help="Number of phases to measure for non-exhaustive qday curves.",
    )
    parser.add_argument(
        "--sample-strategy",
        choices=["prefix", "random"],
        default="prefix",
        help="Sampling strategy for non-exhaustive qday curves.",
    )
    parser.add_argument(
        "--sample-seed",
        type=int,
        default=20260625,
        help="Base deterministic seed for qday random sampling.",
    )
    parser.add_argument(
        "--exhaustive-under",
        type=int,
        default=150000,
        help="Run full orbit enumeration for qday curves with subgroup order at or below this value.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.qday_json:
        suite = benchmark_qday_file(
            Path(args.qday_json),
            bit_min=args.bit_min,
            bit_max=args.bit_max,
            sample_size=args.sample_size,
            exhaustive_under=args.exhaustive_under,
            epsilon=args.epsilon,
            sample_strategy=args.sample_strategy,
            sample_seed=args.sample_seed,
        )
        paths = write_qday_outputs(suite, Path(args.outdir))
        print("Qday observable ECC bench complete.")
        print(f"Curves valid: {suite.curves_valid}/{suite.curves_total}")
        print(f"Markdown: {paths['markdown']}")
        print(f"JSON: {paths['json']}")
        print(f"CSV: {paths['csv']}")
        return

    result = benchmark_curve(epsilon=args.epsilon)
    paths = write_outputs(result, Path(args.outdir))
    print("Observable ECC bench complete.")
    print(f"Paper v0.2 rows match: {result.paper_v02_rows_match}")
    print(f"Recurrence failures: {result.recurrence_checks.generator_recurrence_failures}")
    print(f"Markdown: {paths['markdown']}")
    print(f"JSON: {paths['json']}")
    print(f"CSV: {paths['csv']}")


if __name__ == "__main__":
    main()
