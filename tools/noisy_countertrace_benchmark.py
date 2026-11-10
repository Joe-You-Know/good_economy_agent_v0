"""Synthetic noisy countertrace benchmark.

Safe scope:
- Local synthetic traces only.
- No browser, wallet, OS process, external service, network traffic, passive
  tracing, credential access, key sweeping, or transaction logic.

Purpose:
- Measure how much noise a rank-bearing construction trace can tolerate.
- Compare primary trace only, countertrace only, and fused recovery when an
  independent countertrace channel is available.
- Include a toy ECDSA/RFC6979-style nonce case where recovering noisy
  countertrace for k recovers d in a controlled toy model.

This benchmark does not prove physical capture fidelity. It tests the
post-capture math: if a trace has been converted into noisy symbolic ledger
events, how much corruption can recovery tolerate?
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
from dataclasses import asdict, dataclass
from itertools import product
from typing import Iterable, Sequence


DEFAULT_OUTDIR = "outputs/work_packages/noisy_countertrace_benchmark_2026-06-19"
DEFAULT_SECRET = "face"
DEFAULT_ALPHABET = "abcdef"
DEFAULT_TRIALS = 60


Symbol = tuple[str, int]


@dataclass(frozen=True)
class NoiseProfile:
    name: str
    substitution: float
    dropout: float
    insertion: float


@dataclass(frozen=True)
class RecoveryResult:
    model: str
    profile: str
    mode: str
    trials: int
    successes: int
    unique_recoveries: int
    success_rate: float
    unique_rate: float
    average_top_ties: float
    average_best_distance: float
    notes: str


NOISE_PROFILES = [
    NoiseProfile("clean", 0.00, 0.00, 0.00),
    NoiseProfile("light", 0.02, 0.02, 0.01),
    NoiseProfile("moderate", 0.05, 0.05, 0.02),
    NoiseProfile("heavy", 0.10, 0.08, 0.04),
    NoiseProfile("severe", 0.18, 0.12, 0.06),
    NoiseProfile("extreme", 0.28, 0.18, 0.10),
]


def nand(a: int, b: int) -> int:
    return 1 - (a & b)


def xor_nand_event(a: int, b: int, prev: int) -> tuple[int, int, int, int]:
    n1 = nand(a, b)
    n2 = nand(a, n1)
    n3 = nand(b, n1)
    out = nand(n2, n3)
    flips = sum(1 for v in (n1, n2, n3, out) if v != prev)
    weighted = n1 + 2 * n2 + 4 * n3 + 8 * out
    curvature = (3 * flips + 5 * weighted + 7 * a + 11 * b + 13 * prev) % 31
    return out, flips, weighted, curvature


def deterministic_mask_bit(index: int, bit_pos: int, seed: int = 20260619) -> int:
    # A tiny deterministic mask stream for reproducible synthetic traces.
    x = (1103515245 * (seed + 97 * index + 7919 * bit_pos) + 12345) & 0x7FFFFFFF
    return (x >> 9) & 1


def char_rank(ch: str, alphabet: str = DEFAULT_ALPHABET) -> int:
    return alphabet.index(ch)


def rank_to_bits(rank: int, width: int = 3) -> list[int]:
    return [(rank >> i) & 1 for i in range(width)]


def all_candidates(length: int, alphabet: str) -> list[str]:
    return ["".join(chars) for chars in product(alphabet, repeat=length)]


def primary_trace(secret: str, alphabet: str = DEFAULT_ALPHABET) -> list[Symbol]:
    """Coarse protocol-adjacent trace: rank modulo 3, not full character."""
    return [("primary_mod3", char_rank(ch, alphabet) % 3) for ch in secret]


def counter_trace(secret: str, alphabet: str = DEFAULT_ALPHABET) -> list[Symbol]:
    """Synthetic construction countertrace from masked XOR/NAND events."""
    events: list[Symbol] = []
    prev = 0
    for index, ch in enumerate(secret):
        for bit_pos, secret_bit in enumerate(rank_to_bits(char_rank(ch, alphabet))):
            mask_bit = deterministic_mask_bit(index, bit_pos)
            masked, flips1, weighted1, curvature1 = xor_nand_event(secret_bit, mask_bit, prev)
            recovered, flips2, weighted2, curvature2 = xor_nand_event(masked, mask_bit, masked)
            prev = recovered
            # Use a compact symbolic emission. It is not the secret bit label.
            events.append(("counter", (flips1 * 37 + weighted1 * 11 + curvature1 * 5 + flips2 * 3 + weighted2 + curvature2) % 257))
    return events


def trace_vocab(candidates: Sequence[str], trace_fn) -> list[Symbol]:
    vocab = sorted({sym for cand in candidates for sym in trace_fn(cand)})
    return vocab


def degrade_trace(trace: Sequence[Symbol], vocab: Sequence[Symbol], profile: NoiseProfile, rng: random.Random) -> list[Symbol]:
    out: list[Symbol] = []
    for sym in trace:
        if rng.random() < profile.dropout:
            continue
        observed = sym
        if rng.random() < profile.substitution:
            choices = [v for v in vocab if v != sym]
            observed = rng.choice(choices) if choices else sym
        out.append(observed)
        if rng.random() < profile.insertion:
            out.append(rng.choice(vocab))
    return out


def edit_distance(a: Sequence[Symbol], b: Sequence[Symbol]) -> int:
    prev = list(range(len(b) + 1))
    for i, av in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, bv in enumerate(b, 1):
            cost = 0 if av == bv else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[-1]


def recover_string(
    candidates: Sequence[str],
    observed_primary: Sequence[Symbol],
    observed_counter: Sequence[Symbol],
    mode: str,
) -> tuple[list[str], int]:
    scored: list[tuple[int, str]] = []
    for cand in candidates:
        score = 0
        if mode in {"primary", "fused"}:
            score += edit_distance(primary_trace(cand), observed_primary)
        if mode in {"counter", "fused"}:
            score += edit_distance(counter_trace(cand), observed_counter)
        scored.append((score, cand))
    best = min(score for score, _ in scored)
    return [cand for score, cand in scored if score == best], best


def run_string_benchmark(trials: int, seed: int) -> list[RecoveryResult]:
    candidates = all_candidates(len(DEFAULT_SECRET), DEFAULT_ALPHABET)
    primary_vocab = trace_vocab(candidates, primary_trace)
    counter_vocab = trace_vocab(candidates, counter_trace)
    rows: list[RecoveryResult] = []

    for profile_index, profile in enumerate(NOISE_PROFILES):
        for mode_index, mode in enumerate(("primary", "counter", "fused")):
            successes = 0
            unique = 0
            tie_counts: list[int] = []
            best_distances: list[int] = []
            for trial in range(trials):
                rng = random.Random(seed + 1009 * trial + 100003 * profile_index + 1000003 * mode_index)
                observed_primary = degrade_trace(primary_trace(DEFAULT_SECRET), primary_vocab, profile, rng)
                observed_counter = degrade_trace(counter_trace(DEFAULT_SECRET), counter_vocab, profile, rng)
                winners, distance = recover_string(candidates, observed_primary, observed_counter, mode)
                tie_counts.append(len(winners))
                best_distances.append(distance)
                if DEFAULT_SECRET in winners:
                    successes += 1
                if winners == [DEFAULT_SECRET]:
                    unique += 1
            rows.append(
                RecoveryResult(
                    model="string_countertrace",
                    profile=profile.name,
                    mode=mode,
                    trials=trials,
                    successes=successes,
                    unique_recoveries=unique,
                    success_rate=successes / trials,
                    unique_rate=unique / trials,
                    average_top_ties=sum(tie_counts) / trials,
                    average_best_distance=sum(best_distances) / trials,
                    notes="primary is coarse; countertrace is independent construction emission; fused sums both edit distances",
                )
            )
    return rows


# Toy ECDSA/RFC6979-style constants from the local controlled demo.
TOY_N = 229
TOY_SECRET_D = 137
TOY_Z = 120
TOY_R = 67
TOY_S = 68
TOY_K = 194


def inv_mod(x: int, m: int) -> int:
    return pow(x % m, -1, m)


def recover_d_from_k(k: int) -> int:
    return ((TOY_S * k - TOY_Z) * inv_mod(TOY_R, TOY_N)) % TOY_N


def nonce_countertrace(k: int, bit_width: int = 8) -> list[Symbol]:
    events: list[Symbol] = []
    prev = 0
    for bit_pos in range(bit_width):
        k_bit = (k >> bit_pos) & 1
        mask_bit = deterministic_mask_bit(999, bit_pos)
        masked, flips1, weighted1, curvature1 = xor_nand_event(k_bit, mask_bit, prev)
        recovered, flips2, weighted2, curvature2 = xor_nand_event(masked, mask_bit, masked)
        prev = recovered
        events.append(("nonce_counter", (flips1 * 41 + weighted1 * 13 + curvature1 * 7 + flips2 * 5 + weighted2 + curvature2) % 257))
    return events


def run_ecdsa_nonce_benchmark(trials: int, seed: int) -> list[RecoveryResult]:
    candidates = list(range(1, TOY_N))
    vocab = sorted({sym for k in candidates for sym in nonce_countertrace(k)})
    rows: list[RecoveryResult] = []
    clean = nonce_countertrace(TOY_K)

    for profile_index, profile in enumerate(NOISE_PROFILES):
        successes = 0
        unique = 0
        tie_counts: list[int] = []
        best_distances: list[int] = []
        for trial in range(trials):
            rng = random.Random(seed + 50021 * trial + 300007 * profile_index)
            observed = degrade_trace(clean, vocab, profile, rng)
            scored = [(edit_distance(nonce_countertrace(k), observed), k) for k in candidates]
            best = min(score for score, _ in scored)
            winners = [k for score, k in scored if score == best]
            tie_counts.append(len(winners))
            best_distances.append(best)
            recovered_secret = [recover_d_from_k(k) for k in winners]
            if TOY_SECRET_D in recovered_secret:
                successes += 1
            if winners == [TOY_K]:
                unique += 1
        rows.append(
            RecoveryResult(
                model="toy_ecdsa_nonce_countertrace",
                profile=profile.name,
                mode="counter",
                trials=trials,
                successes=successes,
                unique_recoveries=unique,
                success_rate=successes / trials,
                unique_rate=unique / trials,
                average_top_ties=sum(tie_counts) / trials,
                average_best_distance=sum(best_distances) / trials,
                notes="noisy synthetic nonce countertrace; success means recovered k implies recovered d",
            )
        )
    return rows


def write_outputs(outdir: str, rows: Sequence[RecoveryResult], trials: int, seed: int) -> None:
    os.makedirs(outdir, exist_ok=True)
    json_path = os.path.join(outdir, "noisy_countertrace_benchmark.json")
    csv_path = os.path.join(outdir, "noisy_countertrace_benchmark.csv")
    md_path = os.path.join(outdir, "noisy_countertrace_benchmark_summary.md")

    report = {
        "scope": "local synthetic noisy trace benchmark only; no passive tracing or third-party observation",
        "trials_per_profile": trials,
        "seed": seed,
        "noise_profiles": [asdict(p) for p in NOISE_PROFILES],
        "rows": [asdict(r) for r in rows],
        "interpretation_boundary": [
            "Validates post-capture symbolic recovery under controlled noise.",
            "Does not validate passive browser tracing.",
            "Does not validate EM/power/cache capture fidelity.",
            "Does not validate raw NAND-packet segmentation from physical traces.",
        ],
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    def table_for(model: str) -> str:
        selected = [r for r in rows if r.model == model]
        lines = [
            "| profile | mode | success rate | unique rate | avg top ties | avg best distance |",
            "|---|---|---:|---:|---:|---:|",
        ]
        for r in selected:
            lines.append(
                f"| {r.profile} | {r.mode} | {r.success_rate:.3f} | {r.unique_rate:.3f} | "
                f"{r.average_top_ties:.2f} | {r.average_best_distance:.2f} |"
            )
        return "\n".join(lines)

    summary = f"""# Noisy countertrace benchmark

Date: 2026-06-19

Scope:
- Local synthetic noisy traces only.
- No browser, wallet, OS process, external service, network traffic, passive tracing, credential access, key sweeping, or transaction logic.
- Countertrace is modeled as an already-available symbolic observation channel.

Trials per profile: `{trials}`
Seed: `{seed}`

## String countertrace model

Secret: `{DEFAULT_SECRET}`
Alphabet: `{DEFAULT_ALPHABET}`

The primary trace is intentionally coarse. The countertrace is an independent synthetic construction-emission sequence. Fused recovery sums both edit-distance scores.

{table_for("string_countertrace")}

## Toy ECDSA nonce countertrace model

Toy signature constants:
- `d={TOY_SECRET_D}`
- `k={TOY_K}`
- `r={TOY_R}`
- `s={TOY_S}`
- `z={TOY_Z}`

Success means the noisy countertrace recovered a nonce candidate that implies the controlled private scalar.

{table_for("toy_ecdsa_nonce_countertrace")}

## Interpretation

This validates a post-capture claim: when countertrace is available as a symbolic ledger channel, recovery can tolerate controlled substitution, dropout, and insertion noise up to measurable thresholds.

This does not validate passive tracing, physical capture fidelity, browser observation, wallet observation, or raw physical-to-symbolic segmentation.
"""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(summary)


def print_rows(rows: Sequence[RecoveryResult]) -> None:
    print("Noisy countertrace benchmark")
    print("=" * 78)
    print("Scope: local synthetic traces only; no passive tracing or third-party observation.")
    print(f"{'model':31} {'profile':10} {'mode':8} {'succ':>6} {'uniq':>6} {'ties':>8} {'dist':>8}")
    for r in rows:
        print(
            f"{r.model[:31]:31} {r.profile:10} {r.mode:8} "
            f"{r.success_rate:6.3f} {r.unique_rate:6.3f} "
            f"{r.average_top_ties:8.2f} {r.average_best_distance:8.2f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Safe local synthetic noisy countertrace benchmark.")
    parser.add_argument("--run-all", action="store_true")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=int, default=20260619)
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR)
    args = parser.parse_args()

    if not args.run_all:
        parser.print_help()
        return
    if args.trials <= 0:
        raise ValueError("trials must be positive")

    rows = run_string_benchmark(args.trials, args.seed)
    rows.extend(run_ecdsa_nonce_benchmark(args.trials, args.seed))
    write_outputs(args.outdir, rows, args.trials, args.seed)
    print_rows(rows)
    print("\nOutputs:")
    print("  " + os.path.join(args.outdir, "noisy_countertrace_benchmark_summary.md"))
    print("  " + os.path.join(args.outdir, "noisy_countertrace_benchmark.json"))
    print("  " + os.path.join(args.outdir, "noisy_countertrace_benchmark.csv"))


if __name__ == "__main__":
    main()
