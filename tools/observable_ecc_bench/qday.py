from __future__ import annotations

import csv
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .bench import ObservableMetric, fiber_metric
from .curve import Curve, Point, add, mul, on_curve, orbit, transition_ledger, transition_ledger_for_points, transition_ledgers


QDAY_OBSERVABLES = [
    "point",
    "compressed_point",
    "x",
    "transition_schema",
    "denominator",
    "inverse_lift",
    "ratio_ledger",
    "small_x_category",
]


@dataclass(frozen=True)
class QdayCurveValidation:
    bit_length: int
    prime_field_probable_prime: bool
    generator_on_curve: bool
    public_key_on_curve: bool
    private_key_maps_to_public_key: bool
    subgroup_order_maps_generator_to_infinity: bool
    curve_order_matches_subgroup_times_cofactor: bool
    declared_subgroup_order: int
    declared_curve_order: int
    cofactor: int
    valid: bool
    reasons: list[str]


@dataclass(frozen=True)
class QdayCurveBenchmark:
    bit_length: int
    curve: dict[str, object]
    validation: QdayCurveValidation
    mode: str
    phases_measured: int
    full_order_verified_by_enumeration: bool
    sample_strategy: str
    sample_seed: int | None
    sampled_phase_preview: list[int]
    observables: list[ObservableMetric]
    recurrence_failures: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "bit_length": self.bit_length,
            "curve": self.curve,
            "validation": asdict(self.validation),
            "mode": self.mode,
            "phases_measured": self.phases_measured,
            "full_order_verified_by_enumeration": self.full_order_verified_by_enumeration,
            "sample_strategy": self.sample_strategy,
            "sample_seed": self.sample_seed,
            "sampled_phase_preview": self.sampled_phase_preview,
            "observables": [asdict(metric) for metric in self.observables],
            "recurrence_failures": self.recurrence_failures,
        }


@dataclass(frozen=True)
class QdayBenchmarkSuite:
    source_json: str
    safety_scope: str
    bit_min: int
    bit_max: int
    sample_size: int
    exhaustive_under: int
    sample_strategy: str
    sample_seed: int
    curves_total: int
    curves_valid: int
    curves_invalid: int
    results: list[QdayCurveBenchmark]

    def to_dict(self) -> dict[str, object]:
        return {
            "source_json": self.source_json,
            "safety_scope": self.safety_scope,
            "bit_min": self.bit_min,
            "bit_max": self.bit_max,
            "sample_size": self.sample_size,
            "exhaustive_under": self.exhaustive_under,
            "sample_strategy": self.sample_strategy,
            "sample_seed": self.sample_seed,
            "curves_total": self.curves_total,
            "curves_valid": self.curves_valid,
            "curves_invalid": self.curves_invalid,
            "results": [result.to_dict() for result in self.results],
        }


def parse_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(f"cannot parse integer from {value!r}")


def parse_point(value: Any) -> Point:
    if value is None:
        return None
    if not isinstance(value, list | tuple) or len(value) != 2:
        raise TypeError(f"point must be a two-item list, got {value!r}")
    return (parse_int(value[0]), parse_int(value[1]))


def is_probable_prime(n: int) -> bool:
    if n < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for prime in small_primes:
        if n == prime:
            return True
        if n % prime == 0:
            return False

    d = n - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2

    for base in small_primes:
        if base >= n:
            continue
        x = pow(base, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def curve_from_qday_row(row: dict[str, Any]) -> tuple[int, Curve, int, Point, int, int, int]:
    bit_length = parse_int(row["bit_length"])
    prime = parse_int(row["prime"])
    generator = parse_point(row["generator_point"])
    private_key = parse_int(row["private_key"])
    public_key = parse_point(row["public_key"])
    subgroup_order = parse_int(row["subgroup_order"])
    curve_order = parse_int(row["curve_order"])
    cofactor = parse_int(row["cofactor"])
    curve = Curve(
        name=f"qday_{bit_length}_secp256k1_form",
        p=prime,
        a=0,
        b=7,
        generator=generator,
    )
    return bit_length, curve, private_key, public_key, subgroup_order, curve_order, cofactor


def validate_qday_row(row: dict[str, Any]) -> tuple[QdayCurveValidation, Curve]:
    bit_length, curve, private_key, public_key, subgroup_order, curve_order, cofactor = curve_from_qday_row(row)
    reasons: list[str] = []

    prime_ok = is_probable_prime(curve.p)
    generator_ok = on_curve(curve, curve.generator)
    public_ok = on_curve(curve, public_key)
    private_ok = generator_ok and public_ok and mul(curve, private_key) == public_key
    subgroup_ok = generator_ok and mul(curve, subgroup_order) is None
    order_ok = curve_order == subgroup_order * cofactor

    checks = {
        "prime_field_probable_prime": prime_ok,
        "generator_on_curve": generator_ok,
        "public_key_on_curve": public_ok,
        "private_key_maps_to_public_key": private_ok,
        "subgroup_order_maps_generator_to_infinity": subgroup_ok,
        "curve_order_matches_subgroup_times_cofactor": order_ok,
    }
    for name, ok in checks.items():
        if not ok:
            reasons.append(name)

    validation = QdayCurveValidation(
        bit_length=bit_length,
        prime_field_probable_prime=prime_ok,
        generator_on_curve=generator_ok,
        public_key_on_curve=public_ok,
        private_key_maps_to_public_key=private_ok,
        subgroup_order_maps_generator_to_infinity=subgroup_ok,
        curve_order_matches_subgroup_times_cofactor=order_ok,
        declared_subgroup_order=subgroup_order,
        declared_curve_order=curve_order,
        cofactor=cofactor,
        valid=not reasons,
        reasons=reasons,
    )
    return validation, curve


def prefix_points(curve: Curve, phase_count: int) -> list[Point]:
    if phase_count < 1:
        raise ValueError("phase_count must be positive")

    points: list[Point] = [None]
    point: Point = None
    for _ in range(phase_count):
        point = add(curve, point, curve.generator)
        points.append(point)
    return points


def sample_ledgers(curve: Curve, points_with_next: list[Point], phase_count: int):
    return [transition_ledger(curve, points_with_next, phase) for phase in range(phase_count)]


def random_phase_sample(
    curve: Curve,
    subgroup_order: int,
    sample_size: int,
    seed: int,
) -> tuple[list[int], list[Point], list]:
    if subgroup_order <= 2:
        raise ValueError("subgroup_order must exceed 2 for random phase sampling")
    sample_count = min(sample_size, subgroup_order - 2)
    rng = random.Random(seed)
    selected: set[int] = set()
    while len(selected) < sample_count:
        selected.add(rng.randrange(1, subgroup_order - 1))
    phases = sorted(selected)
    points: list[Point] = []
    ledgers = []
    for phase in phases:
        point = mul(curve, phase)
        next_point = add(curve, point, curve.generator)
        points.append(point)
        ledgers.append(
            transition_ledger_for_points(
                curve=curve,
                phase=phase,
                point=point,
                next_point=next_point,
                order=subgroup_order,
            )
        )
    return phases, points, ledgers


def metric_lookup(metrics: list[ObservableMetric]) -> dict[str, ObservableMetric]:
    return {metric.name: metric for metric in metrics}


def curve_benchmarkable(validation: QdayCurveValidation) -> bool:
    return (
        validation.prime_field_probable_prime
        and validation.generator_on_curve
        and validation.subgroup_order_maps_generator_to_infinity
        and validation.curve_order_matches_subgroup_times_cofactor
    )


def benchmark_qday_row(
    row: dict[str, Any],
    sample_size: int,
    exhaustive_under: int,
    epsilon: float,
    observables: list[str] | None = None,
    sample_strategy: str = "prefix",
    sample_seed: int = 20260625,
) -> QdayCurveBenchmark:
    validation, curve = validate_qday_row(row)
    selected_observables = QDAY_OBSERVABLES if observables is None else observables

    if not curve_benchmarkable(validation):
        return QdayCurveBenchmark(
            bit_length=validation.bit_length,
            curve={"name": curve.name, "p": curve.p, "a": curve.a, "b": curve.b, "generator": curve.generator},
            validation=validation,
            mode="invalid_skipped",
            phases_measured=0,
            full_order_verified_by_enumeration=False,
            sample_strategy="none",
            sample_seed=None,
            sampled_phase_preview=[],
            observables=[],
            recurrence_failures={},
        )

    full_order_verified = False
    sampled_phases: list[int] = []
    keypair_warning = not validation.private_key_maps_to_public_key
    if validation.declared_subgroup_order <= exhaustive_under:
        mode = "exhaustive"
        points = orbit(curve)
        full_order_verified = len(points) == validation.declared_subgroup_order
        ledgers = transition_ledgers(curve, points)
        phase_points = points
        active_strategy = "full_orbit"
        active_seed = None
    else:
        if sample_strategy not in {"prefix", "random"}:
            raise ValueError("sample_strategy must be 'prefix' or 'random'")
        active_strategy = sample_strategy
        active_seed = sample_seed + validation.bit_length * 1009
        if sample_strategy == "random":
            mode = "random_sample_keypair_mismatch" if keypair_warning else "random_sample"
            sampled_phases, phase_points, ledgers = random_phase_sample(
                curve=curve,
                subgroup_order=validation.declared_subgroup_order,
                sample_size=sample_size,
                seed=active_seed,
            )
        else:
            mode = "prefix_sample_keypair_mismatch" if keypair_warning else "prefix_sample"
            phase_count = min(sample_size, validation.declared_subgroup_order)
            points_with_next = prefix_points(curve, phase_count)
            phase_points = points_with_next[:phase_count]
            ledgers = sample_ledgers(curve, points_with_next, phase_count)
            sampled_phases = list(range(phase_count))

    metrics = [
        fiber_metric(curve, phase_points, ledgers, observable, epsilon, max_fiber_phases=20)
        for observable in selected_observables
    ]
    failures = {
        "ledger_count_mismatch": 0 if len(phase_points) == len(ledgers) else 1,
        "full_order_mismatch": 0 if (mode != "exhaustive" or full_order_verified) else 1,
    }

    return QdayCurveBenchmark(
        bit_length=validation.bit_length,
        curve={"name": curve.name, "p": curve.p, "a": curve.a, "b": curve.b, "generator": curve.generator},
        validation=validation,
        mode=mode,
        phases_measured=len(phase_points),
        full_order_verified_by_enumeration=full_order_verified,
        sample_strategy=active_strategy,
        sample_seed=active_seed,
        sampled_phase_preview=sampled_phases[:20],
        observables=metrics,
        recurrence_failures=failures,
    )


def load_qday_rows(path: Path, bit_min: int, bit_max: int) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    selected = []
    for row in rows:
        bit_length = parse_int(row["bit_length"])
        if bit_min <= bit_length <= bit_max:
            selected.append(row)
    return selected


def benchmark_qday_file(
    path: Path,
    bit_min: int = 17,
    bit_max: int = 28,
    sample_size: int = 4096,
    exhaustive_under: int = 150000,
    epsilon: float = 0.125,
    sample_strategy: str = "prefix",
    sample_seed: int = 20260625,
) -> QdayBenchmarkSuite:
    rows = load_qday_rows(path, bit_min, bit_max)
    results = [
        benchmark_qday_row(
            row,
            sample_size=sample_size,
            exhaustive_under=exhaustive_under,
            epsilon=epsilon,
            sample_strategy=sample_strategy,
            sample_seed=sample_seed,
        )
        for row in rows
    ]
    return QdayBenchmarkSuite(
        source_json=str(path),
        safety_scope=(
            "Local validation and finite-sample observable analysis only; no live targets, no puzzle solving, "
            "no wallet/key recovery, no network access."
        ),
        bit_min=bit_min,
        bit_max=bit_max,
        sample_size=sample_size,
        exhaustive_under=exhaustive_under,
        sample_strategy=sample_strategy,
        sample_seed=sample_seed,
        curves_total=len(results),
        curves_valid=sum(1 for result in results if curve_benchmarkable(result.validation)),
        curves_invalid=sum(1 for result in results if not curve_benchmarkable(result.validation)),
        results=results,
    )


def generate_qday_markdown(suite: QdayBenchmarkSuite) -> str:
    lines: list[str] = []
    lines.append("# Qday Observable ECC Bench Report")
    lines.append("")
    lines.append(f"Source JSON: `{suite.source_json}`")
    lines.append("")
    lines.append(f"Safety scope: {suite.safety_scope}")
    lines.append("")
    lines.append(f"Bit range: `{suite.bit_min}-{suite.bit_max}`")
    lines.append(f"Sample size: `{suite.sample_size}`")
    lines.append(f"Exhaustive under: `{suite.exhaustive_under}`")
    lines.append(f"Sample strategy: `{suite.sample_strategy}`")
    lines.append(f"Sample seed: `{suite.sample_seed}`")
    lines.append("")
    lines.append("## Validation Summary")
    lines.append("")
    lines.append(f"- Curves tested: `{suite.curves_total}`")
    lines.append(f"- Valid curves: `{suite.curves_valid}`")
    lines.append(f"- Invalid curves: `{suite.curves_invalid}`")
    lines.append("")
    lines.append("## Observable Summary")
    lines.append("")
    lines.append("| Bits | Status | Mode | Phases | Order | x N_eff | Ratio N_eff | Ratio Max Fiber | Small-x N_eff |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|")
    for result in suite.results:
        metrics = metric_lookup(result.observables)
        x_metric = metrics.get("x")
        ratio_metric = metrics.get("ratio_ledger")
        small_metric = metrics.get("small_x_category")
        if curve_benchmarkable(result.validation) and result.validation.valid:
            status = "valid"
        elif curve_benchmarkable(result.validation):
            status = "curve_valid_keypair_mismatch"
        else:
            status = "invalid"
        lines.append(
            "| {bits} | {status} | {mode} | {phases} | {order} | {x_neff} | {ratio_neff} | {ratio_max} | {small_neff} |".format(
                bits=result.bit_length,
                status=status,
                mode=result.mode,
                phases=result.phases_measured,
                order=result.validation.declared_subgroup_order,
                x_neff=f"{x_metric.effective_support:.6g}" if x_metric else "n/a",
                ratio_neff=f"{ratio_metric.effective_support:.6g}" if ratio_metric else "n/a",
                ratio_max=ratio_metric.max_fiber_size if ratio_metric else "n/a",
                small_neff=f"{small_metric.effective_support:.6g}" if small_metric else "n/a",
            )
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Rows marked `valid` satisfy all local checks. Rows marked `curve_valid_keypair_mismatch` pass the "
        "curve/generator/order checks but the supplied private key does not map to the supplied public key; "
        "observable sampling can still run because it does not use that keypair."
    )
    lines.append("")
    lines.append(
        "Rows marked `prefix_sample` or `random_sample` report effective support over measured samples only. "
        "They are useful for detecting collisions and transition-category collapse, but they are not full-orbit claims."
    )
    lines.append("")
    lines.append(
        "This benchmark does not solve BTC puzzles, recover private keys, inspect wallets, or validate any passive capture channel."
    )
    lines.append("")
    return "\n".join(lines)


def write_qday_outputs(suite: QdayBenchmarkSuite, outdir: Path) -> dict[str, str]:
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / "qday_observable_ecc_summary.json"
    md_path = outdir / "qday_observable_ecc_summary.md"
    csv_path = outdir / "qday_observable_ecc_summary.csv"

    json_path.write_text(json.dumps(suite.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(generate_qday_markdown(suite), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "bit_length",
                "valid",
                "mode",
                "sample_strategy",
                "sample_seed",
                "phases_measured",
                "declared_subgroup_order",
                "x_effective_support",
                "ratio_ledger_effective_support",
                "ratio_ledger_max_fiber",
                "small_x_effective_support",
            ],
        )
        writer.writeheader()
        for result in suite.results:
            metrics = metric_lookup(result.observables)
            x_metric = metrics.get("x")
            ratio_metric = metrics.get("ratio_ledger")
            small_metric = metrics.get("small_x_category")
            writer.writerow(
                {
                    "bit_length": result.bit_length,
                    "valid": result.validation.valid,
                    "mode": result.mode,
                    "sample_strategy": result.sample_strategy,
                    "sample_seed": result.sample_seed if result.sample_seed is not None else "",
                    "phases_measured": result.phases_measured,
                    "declared_subgroup_order": result.validation.declared_subgroup_order,
                    "x_effective_support": x_metric.effective_support if x_metric else "",
                    "ratio_ledger_effective_support": ratio_metric.effective_support if ratio_metric else "",
                    "ratio_ledger_max_fiber": ratio_metric.max_fiber_size if ratio_metric else "",
                    "small_x_effective_support": small_metric.effective_support if small_metric else "",
                }
            )

    return {"json": str(json_path), "markdown": str(md_path), "csv": str(csv_path)}
