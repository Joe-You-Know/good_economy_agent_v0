from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from .curve import (
    Curve,
    Point,
    TransitionLedger,
    add,
    inv_mod,
    orbit,
    point_key,
    point_x_key,
    toy_curve_97,
    transition_ledgers,
)


DEFAULT_OBSERVABLES = [
    "opaque_label",
    "point",
    "compressed_point",
    "x",
    "x_state",
    "transition_schema",
    "denominator",
    "inverse_lift",
    "ratio_ledger",
    "small_x_category",
]


PAPER_V02_ROWS = [
    {"d": 1, "op": "dbl", "D": 11, "U": 3, "V": 53, "m": 6, "lambda": 62, "ell": 1, "x_next": 63, "L": 37, "omega": 53},
    {"d": 2, "op": "+G", "D": 33, "U": 2, "V": 50, "m": 17, "lambda": 3, "ell": 1, "x_next": 44, "L": -2, "omega": 50},
    {"d": 3, "op": "+G", "D": 52, "U": 49, "V": 28, "m": 15, "lambda": 14, "ell": 14, "x_next": 56, "L": 0, "omega": 28},
    {"d": 4, "op": "+G", "D": 40, "U": 33, "V": 17, "m": 7, "lambda": 76, "ell": 5, "x_next": 95, "L": 57, "omega": 17},
    {"d": 5, "op": "+G", "D": 1, "U": 32, "V": 1, "m": 0, "lambda": 32, "ell": 0, "x_next": 57, "L": 8, "omega": 1},
    {"d": 6, "op": "+G", "D": 39, "U": 24, "V": 5, "m": 2, "lambda": 23, "ell": 1, "x_next": 85, "L": 3, "omega": 15},
    {"d": 7, "op": "+G", "D": 11, "U": 49, "V": 53, "m": 6, "lambda": 75, "ell": 26, "x_next": 12, "L": 56, "omega": 53},
    {"d": 8, "op": "+G", "D": 84, "U": 16, "V": 82, "m": 71, "lambda": 51, "ell": 13, "x_next": 68, "L": 25, "omega": 328},
    {"d": 9, "op": "+G", "D": 28, "U": 38, "V": 52, "m": 15, "lambda": 36, "ell": 20, "x_next": 65, "L": 11, "omega": 104},
]


@dataclass(frozen=True)
class ObservableMetric:
    name: str
    phases: int
    distinct_values: int
    collision_mass: float
    effective_support: float
    max_fiber_size: int
    singleton_fibers: int
    largest_fibers: list[dict[str, object]]


@dataclass(frozen=True)
class RecurrenceChecks:
    doubling_checked: int
    doubling_failures: int
    generator_recurrence_checked: int
    generator_recurrence_failures: int
    boundary_phases: list[int]


@dataclass(frozen=True)
class BenchmarkResult:
    source_paper: str
    safety_scope: str
    curve: dict[str, object]
    order: int
    observables: list[ObservableMetric]
    recurrence_checks: RecurrenceChecks
    paper_v02_rows_match: bool
    paper_v02_row_diffs: list[dict[str, object]]
    transition_rows: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        return {
            "source_paper": self.source_paper,
            "safety_scope": self.safety_scope,
            "curve": self.curve,
            "order": self.order,
            "observables": [asdict(metric) for metric in self.observables],
            "recurrence_checks": asdict(self.recurrence_checks),
            "paper_v02_rows_match": self.paper_v02_rows_match,
            "paper_v02_row_diffs": self.paper_v02_row_diffs,
            "transition_rows": self.transition_rows,
        }


def stable_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def ratio_pair(left: int | None, right: int | None) -> tuple[str, int, int] | tuple[str]:
    if left is None or right is None:
        return ("boundary",)
    return ("ratio", left, right)


def observable_value(
    curve: Curve,
    points: list[Point],
    ledgers: list[TransitionLedger],
    phase: int,
    name: str,
    epsilon: float,
) -> Any:
    n = len(points)
    point = points[phase]
    ledger = ledgers[phase]
    p = curve.p

    if name == "opaque_label":
        return ("opaque", phase)
    if name == "point":
        return point_key(point)
    if name == "compressed_point":
        if point is None:
            return ("inf",)
        return ("compressed", point[0], point[1] & 1)
    if name == "x":
        return point_x_key(point)
    if name == "x_state":
        return ("x_state", point_x_key(points[(phase - 1) % n]), point_x_key(point))
    if name == "transition_schema":
        return ("schema", ledger.op, ledger.boundary)
    if name == "denominator":
        return ("D", ledger.D, ledger.boundary)
    if name == "inverse_lift":
        return ("inverse", ledger.D, ledger.V, ledger.m, ledger.boundary)
    if name == "ratio_ledger":
        return (
            "ratio_ledger",
            ledger.op,
            ratio_pair(ledger.U, ledger.D),
            ratio_pair(ledger.m, ledger.V),
            ratio_pair(ledger.lambda_value, None if ledger.ell is None else ledger.ell * p),
            ratio_pair(ledger.x_next, None if ledger.L is None else ledger.L * p),
            ledger.omega,
            ledger.sign_L,
            ledger.boundary,
        )
    if name == "small_x_category":
        is_small = None if ledger.x_next is None else ledger.x_next < epsilon * p
        return (
            "small_x_category",
            is_small,
            ratio_pair(ledger.U, ledger.D),
            ratio_pair(ledger.m, ledger.V),
            ratio_pair(ledger.lambda_value, None if ledger.ell is None else ledger.ell * p),
            ratio_pair(ledger.x_next, None if ledger.L is None else ledger.L * p),
            ledger.omega,
            ledger.sign_L,
            ledger.boundary,
        )
    raise ValueError(f"unknown observable {name!r}")


def fiber_metric(
    curve: Curve,
    points: list[Point],
    ledgers: list[TransitionLedger],
    observable: str,
    epsilon: float,
    max_fiber_phases: int | None = None,
) -> ObservableMetric:
    fibers: dict[str, list[int]] = defaultdict(list)
    values_by_key: dict[str, Any] = {}
    for phase in range(len(points)):
        value = observable_value(curve, points, ledgers, phase, observable, epsilon)
        key = stable_key(value)
        values_by_key[key] = value
        fibers[key].append(phase)

    n = len(points)
    size_sum = sum(len(phases) * len(phases) for phases in fibers.values())
    collision_mass = size_sum / (n * n)
    effective_support = (n * n) / size_sum
    largest = sorted(fibers.items(), key=lambda item: (-len(item[1]), item[0]))[:5]

    return ObservableMetric(
        name=observable,
        phases=n,
        distinct_values=len(fibers),
        collision_mass=collision_mass,
        effective_support=effective_support,
        max_fiber_size=max(len(phases) for phases in fibers.values()),
        singleton_fibers=sum(1 for phases in fibers.values() if len(phases) == 1),
        largest_fibers=[
            {
                "value": values_by_key[key],
                "size": len(phases),
                "phases": phases if max_fiber_phases is None else phases[:max_fiber_phases],
                "phases_truncated": False if max_fiber_phases is None else len(phases) > max_fiber_phases,
            }
            for key, phases in largest
        ],
    )


def x_doubling_formula(curve: Curve, point: Point) -> int | None:
    if point is None:
        return None
    x, _y = point
    denominator = (4 * curve.f(x)) % curve.p
    if denominator == 0:
        return None
    numerator = (x**4 - 2 * curve.a * x * x - 8 * curve.b * x + curve.a * curve.a) % curve.p
    return (numerator * inv_mod(denominator, curve.p)) % curve.p


def x_generator_recurrence(curve: Curve, prev_point: Point, point: Point) -> int | None:
    if prev_point is None or point is None or curve.generator is None:
        return None
    x_prev = prev_point[0]
    x = point[0]
    xg = curve.generator[0]
    denominator = ((xg - x) * (xg - x)) % curve.p
    if denominator == 0:
        return None
    value = (
        2 * (curve.f(x) + curve.f(xg)) * inv_mod(denominator, curve.p)
        - 2 * (x + xg)
        - x_prev
    )
    return value % curve.p


def run_recurrence_checks(curve: Curve, points: list[Point], ledgers: list[TransitionLedger]) -> RecurrenceChecks:
    doubling_checked = 0
    doubling_failures = 0
    recurrence_checked = 0
    recurrence_failures = 0
    boundary_phases: list[int] = []

    for phase, point in enumerate(points):
        ledger = ledgers[phase]
        if ledger.boundary:
            boundary_phases.append(phase)

        expected_double = add(curve, point, point)
        formula_x = x_doubling_formula(curve, point)
        if formula_x is not None and expected_double is not None:
            doubling_checked += 1
            if formula_x != expected_double[0]:
                doubling_failures += 1

        if phase == 0:
            continue
        next_point = points[(phase + 1) % len(points)]
        recurrence_x = x_generator_recurrence(curve, points[(phase - 1) % len(points)], point)
        if recurrence_x is not None and next_point is not None:
            recurrence_checked += 1
            if recurrence_x != next_point[0]:
                recurrence_failures += 1

    return RecurrenceChecks(
        doubling_checked=doubling_checked,
        doubling_failures=doubling_failures,
        generator_recurrence_checked=recurrence_checked,
        generator_recurrence_failures=recurrence_failures,
        boundary_phases=boundary_phases,
    )


def validate_paper_v02_rows(ledgers: list[TransitionLedger] | None = None) -> tuple[bool, list[dict[str, object]]]:
    if ledgers is None:
        curve = toy_curve_97()
        ledgers = transition_ledgers(curve, orbit(curve))

    diffs: list[dict[str, object]] = []
    for expected in PAPER_V02_ROWS:
        actual = ledgers[int(expected["d"])].paper_row()
        if actual != expected:
            diffs.append({"phase": expected["d"], "expected": expected, "actual": actual})
    return not diffs, diffs


def benchmark_curve(
    curve: Curve | None = None,
    observables: list[str] | None = None,
    epsilon: float = 0.125,
    source_paper: str = "constructive_ecc_security_assumption_v0_2",
) -> BenchmarkResult:
    curve = toy_curve_97() if curve is None else curve
    selected_observables = DEFAULT_OBSERVABLES if observables is None else observables
    points = orbit(curve)
    ledgers = transition_ledgers(curve, points)
    metrics = [fiber_metric(curve, points, ledgers, name, epsilon) for name in selected_observables]
    checks = run_recurrence_checks(curve, points, ledgers)
    paper_match, paper_diffs = validate_paper_v02_rows(ledgers)
    transition_rows = [ledgers[phase].paper_row() for phase in range(1, min(10, len(ledgers)))]

    return BenchmarkResult(
        source_paper=source_paper,
        safety_scope=(
            "Local toy finite-curve analysis only; no live targets, no browser/process tracing, "
            "no wallet/key recovery, no network access."
        ),
        curve={
            "name": curve.name,
            "p": curve.p,
            "a": curve.a,
            "b": curve.b,
            "generator": curve.generator,
        },
        order=len(points),
        observables=metrics,
        recurrence_checks=checks,
        paper_v02_rows_match=paper_match,
        paper_v02_row_diffs=paper_diffs,
        transition_rows=transition_rows,
    )


def generate_markdown_report(result: BenchmarkResult) -> str:
    lines: list[str] = []
    lines.append("# Observable ECC Bench Report")
    lines.append("")
    lines.append(f"Source paper: `{result.source_paper}`")
    lines.append("")
    lines.append(f"Safety scope: {result.safety_scope}")
    lines.append("")
    lines.append("## Curve")
    lines.append("")
    lines.append(f"- Name: `{result.curve['name']}`")
    lines.append(f"- Field: `F_{result.curve['p']}`")
    lines.append(f"- Equation: `y^2 = x^3 + {result.curve['a']}x + {result.curve['b']}`")
    lines.append(f"- Generator: `{result.curve['generator']}`")
    lines.append(f"- Orbit order: `{result.order}` phases")
    lines.append("")
    lines.append("## Paper v0.2 Regression")
    lines.append("")
    if result.paper_v02_rows_match:
        lines.append("The first nine transition-ledger rows match the v0.2 table.")
    else:
        lines.append("The first nine transition-ledger rows do not match the v0.2 table.")
    lines.append("")
    lines.append("| d | op | D | U | V | m | lambda | ell | x_next | L | omega |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in result.transition_rows:
        lines.append(
            "| {d} | {op} | {D} | {U} | {V} | {m} | {lambda} | {ell} | {x_next} | {L} | {omega} |".format(
                **row
            )
        )
    lines.append("")
    lines.append("## Recurrence Checks")
    lines.append("")
    checks = result.recurrence_checks
    lines.append(f"- Doubling x-law checked: `{checks.doubling_checked}`")
    lines.append(f"- Doubling x-law failures: `{checks.doubling_failures}`")
    lines.append(f"- Generator recurrence checked: `{checks.generator_recurrence_checked}`")
    lines.append(f"- Generator recurrence failures: `{checks.generator_recurrence_failures}`")
    lines.append(f"- Boundary phases: `{checks.boundary_phases}`")
    lines.append("")
    lines.append("## Observable Fibers")
    lines.append("")
    lines.append("| Observable | Distinct | Max Fiber | Singleton Fibers | N_eff | Collision Mass |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for metric in result.observables:
        lines.append(
            f"| `{metric.name}` | {metric.distinct_values} | {metric.max_fiber_size} | "
            f"{metric.singleton_fibers} | {metric.effective_support:.6g} | {metric.collision_mass:.6g} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The benchmark validates the paper's local toy-curve claims: projected operation schemas "
        "collapse many constructive distinctions, while ratio-ledger observables refine the phase "
        "partition. Effective support is a fiber metric, not a proof of practical scalar recovery."
    )
    lines.append("")
    lines.append(
        "This result does not validate passive capture fidelity, browser tracing, production "
        "secp256k1 key recovery, wallet recovery, or public-output-only ECDLP inversion."
    )
    lines.append("")
    return "\n".join(lines)


def write_outputs(result: BenchmarkResult, outdir: Path) -> dict[str, str]:
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / "observable_ecc_bench_summary.json"
    md_path = outdir / "observable_ecc_bench_summary.md"
    csv_path = outdir / "observable_ecc_bench_observables.csv"

    json_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(generate_markdown_report(result), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "name",
                "phases",
                "distinct_values",
                "collision_mass",
                "effective_support",
                "max_fiber_size",
                "singleton_fibers",
            ],
        )
        writer.writeheader()
        for metric in result.observables:
            writer.writerow(
                {
                    "name": metric.name,
                    "phases": metric.phases,
                    "distinct_values": metric.distinct_values,
                    "collision_mass": metric.collision_mass,
                    "effective_support": metric.effective_support,
                    "max_fiber_size": metric.max_fiber_size,
                    "singleton_fibers": metric.singleton_fibers,
                }
            )

    return {
        "json": str(json_path),
        "markdown": str(md_path),
        "csv": str(csv_path),
    }
