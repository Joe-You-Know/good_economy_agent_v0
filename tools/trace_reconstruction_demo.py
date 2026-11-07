"""Safe local trace-reconstruction demo.

This is not spyware and does not observe any browser, wallet, or OS process.
It creates an isolated toy elliptic-curve scalar multiplication, records a
single forward trace of EEA quotient strings for denominator inversions, then
tries to recover the hidden scalar from that trace alone.

The purpose is narrow: validate the internal claim that a sufficiently rich
single forward execution transcript can determine ladder decisions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable


Point = tuple[int, int] | None


P = 9739
A = 497
B = 1768
G: Point = (1804, 5368)
SECRET = 2741
BIT_LENGTH = 12
TRIAL_COUNT = 32


def inv_mod(x: int, p: int = P) -> int:
    return pow(x % p, -1, p)


def on_curve(point: Point) -> bool:
    if point is None:
        return True
    x, y = point
    return (y * y - (x * x * x + A * x + B)) % P == 0


def negate(point: Point) -> Point:
    if point is None:
        return None
    x, y = point
    return (x, (-y) % P)


def add(p1: Point, p2: Point) -> Point:
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if p1 == p2:
        slope = ((3 * x1 * x1 + A) * inv_mod(2 * y1)) % P
    else:
        slope = ((y2 - y1) * inv_mod(x2 - x1)) % P
    x3 = (slope * slope - x1 - x2) % P
    y3 = (slope * (x1 - x3) - y1) % P
    return (x3, y3)


def mul(k: int, point: Point = G) -> Point:
    result: Point = None
    addend = point
    while k:
        if k & 1:
            result = add(result, addend)
        addend = add(addend, addend)
        k >>= 1
    return result


def eea_quotients(denom: int, modulus: int = P) -> list[int]:
    """Return Euclidean quotients for gcd(modulus, denom)."""
    a = modulus
    b = denom % modulus
    if b == 0:
        raise ValueError("denominator is zero")
    quotients: list[int] = []
    while b:
        q, r = divmod(a, b)
        quotients.append(q)
        a, b = b, r
    if a != 1:
        raise ValueError("denominator is not invertible")
    return quotients


def denominator_from_quotients(quotients: Iterable[int], modulus: int = P) -> int:
    """Reconstruct denom from the continued fraction modulus / denom."""
    qs = list(quotients)
    if not qs:
        raise ValueError("empty quotient trace")
    value = Fraction(qs[-1], 1)
    for q in reversed(qs[:-1]):
        value = q + Fraction(1, value)
    if value.numerator != modulus:
        raise ValueError(
            f"quotient trace reconstructed {value.numerator}/{value.denominator}, "
            f"expected numerator {modulus}"
        )
    return value.denominator % modulus


@dataclass(frozen=True)
class DenominatorBlock:
    add_q: tuple[int, ...]
    dbl_q: tuple[int, ...]

    def to_denominators(self) -> tuple[int, int]:
        return (
            denominator_from_quotients(self.add_q),
            denominator_from_quotients(self.dbl_q),
        )


def denominator_block(point: Point) -> tuple[int, int]:
    if point is None:
        raise ValueError("point at infinity has no affine denominator block")
    x, y = point
    d_add = (G[0] - x) % P
    d_dbl = (2 * y) % P
    if d_add == 0 or d_dbl == 0:
        raise ValueError("non-invertible denominator in toy trace")
    return d_add, d_dbl


def trace_block(point: Point) -> DenominatorBlock:
    d_add, d_dbl = denominator_block(point)
    return DenominatorBlock(
        add_q=tuple(eea_quotients(d_add)),
        dbl_q=tuple(eea_quotients(d_dbl)),
    )


def forward_trace(secret: int, bit_length: int = BIT_LENGTH) -> tuple[list[DenominatorBlock], Point]:
    bits = f"{secret:0{bit_length}b}"
    if bits[0] != "1":
        raise ValueError("demo expects a fixed-width scalar with leading MSB set")

    # In a fixed-width ladder, the leading MSB is known to be 1. Starting from
    # G avoids the degenerate first trace block where x_G - x_G == 0.
    state: Point = G
    trace: list[DenominatorBlock] = []
    for bit in bits[1:]:
        state = add(state, state)
        if bit == "1":
            state = add(state, G)
        trace.append(trace_block(state))
    return trace, state


def recover_from_trace(trace: list[DenominatorBlock]) -> tuple[int, str, Point]:
    state: Point = G
    recovered_bits: list[str] = ["1"]
    for index, block in enumerate(trace):
        observed = block.to_denominators()
        candidates: list[tuple[str, Point]] = []
        doubled = add(state, state)
        candidates.append(("0", doubled))
        candidates.append(("1", add(doubled, G)))

        matches = [
            (bit, candidate)
            for bit, candidate in candidates
            if candidate is not None and denominator_block(candidate) == observed
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"trace block {index} produced {len(matches)} candidate matches"
            )
        bit, state = matches[0]
        recovered_bits.append(bit)

    recovered = int("".join(recovered_bits), 2)
    return recovered, "".join(recovered_bits), state


def run_case(secret: int) -> dict[str, object]:
    trace, final_point = forward_trace(secret)
    recovered, recovered_bits, recovered_point = recover_from_trace(trace)
    return {
        "secret_scalar": secret,
        "public_point": final_point,
        "trace_blocks": len(trace),
        "recovered_scalar": recovered,
        "recovered_bits": recovered_bits,
        "recovered_point": recovered_point,
        "scalar_match": recovered == secret,
        "point_match": recovered_point == final_point,
    }


def trial_secrets(count: int, bit_length: int = BIT_LENGTH) -> list[int]:
    lo = 1 << (bit_length - 1)
    span = 1 << (bit_length - 1)
    out: list[int] = []
    x = SECRET
    while len(out) < count:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        candidate = lo + (x % span)
        if candidate not in out:
            out.append(candidate)
    return out


def main() -> None:
    if not on_curve(G):
        raise RuntimeError("bad generator")

    primary = run_case(SECRET)
    trials: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    for secret in trial_secrets(TRIAL_COUNT):
        try:
            trials.append(run_case(secret))
        except Exception as exc:
            skipped.append({"secret_scalar": secret, "reason": str(exc)})

    passed = [
        t for t in trials if bool(t["scalar_match"]) and bool(t["point_match"])
    ]

    result = {
        "demo": "single_forward_trace_reconstruction",
        "scope": "toy_curve_instrumented_local_only",
        "curve": {"p": P, "a": A, "b": B, "G": G},
        "bit_length": BIT_LENGTH,
        "trace_contents": "EEA quotient strings for add/double denominators only",
        "records_secret_bits": False,
        "records_operation_labels": False,
        "primary_case": primary,
        "batch_trials_requested": TRIAL_COUNT,
        "batch_trials_runnable": len(trials),
        "batch_trials_passed": len(passed),
        "batch_trials_failed": len(trials) - len(passed),
        "batch_trials_skipped_degenerate": len(skipped),
        "skipped_degenerate_cases": skipped[:5],
        "claim_validated": (
            "A sufficiently rich single forward denominator/EEA transcript "
            "determines ladder bits in this controlled toy setting."
        ),
        "not_validated": [
            "passive browser/OS tracing",
            "EM/power/cache capture fidelity",
            "real secp256k1 implementation leakage",
            "SHA-256 or RIPEMD-160 inversion",
            "public-output-only inversion",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
