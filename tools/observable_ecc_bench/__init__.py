"""Observable-indexed ECC benchmark tools.

Safe scope: local toy curves only. This package does not inspect browsers,
wallets, processes, networks, accounts, or third-party systems.
"""

from .bench import (
    DEFAULT_OBSERVABLES,
    BenchmarkResult,
    benchmark_curve,
    generate_markdown_report,
    validate_paper_v02_rows,
)
from .curve import Curve, Point, TransitionLedger, toy_curve_97
from .qday import (
    QdayBenchmarkSuite,
    QdayCurveBenchmark,
    benchmark_qday_file,
    validate_qday_row,
)

__all__ = [
    "DEFAULT_OBSERVABLES",
    "BenchmarkResult",
    "Curve",
    "Point",
    "TransitionLedger",
    "QdayBenchmarkSuite",
    "QdayCurveBenchmark",
    "benchmark_curve",
    "benchmark_qday_file",
    "generate_markdown_report",
    "toy_curve_97",
    "validate_qday_row",
    "validate_paper_v02_rows",
]
