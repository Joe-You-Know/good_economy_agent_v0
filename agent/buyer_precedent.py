"""Read-only, source-audited *simulated* procurement decision for codec options.

No purchase, account access, payment, browsing, publication, or model inference.
The buyer is explicitly separated from the product/vendor and may choose a free
alternative. Input mandates are synthetic counterfactuals, never real demand.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

METHODS = ("explicit", "gzip", "constructive")


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _safe_float(value, name):
    val = float(value)
    if not math.isfinite(val) or val < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return val


def load_evidence(summary_path: Path, trial_path: Path, artifacts_dir: Path | None):
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    with open(trial_path, newline="", encoding="utf-8") as fh:
        trial_rows = list(csv.DictReader(fh))
    if not summary.get("all_exact_verified") or not summary.get("full_success"):
        raise ValueError("Benchmark has not reported complete source verification")
    if len(trial_rows) != summary.get("transfers"):
        raise ValueError("Unexpected trial count")
    source = summary["source"]
    manifest = summary["candidate_manifest"]
    if source["source_sha256"] != manifest["source_sha256"] or source["source_bytes"] != manifest["source_bytes"]:
        raise ValueError("Source and manifest disagree")
    if set(manifest["variants"]) != set(METHODS):
        raise ValueError("Methods differ from expected buyer alternatives")
    artifact_check = {"provided": artifacts_dir is not None, "hashes_match_manifest": None,
                      "gzip_independent_roundtrip": None, "constructive_independent_decode": False}
    if artifacts_dir is not None:
        files = {m: Path(artifacts_dir) / manifest["variants"][m]["name"] for m in METHODS}
        for method, path in files.items():
            item = manifest["variants"][method]
            if not path.is_file() or path.stat().st_size != item["artifact_bytes"] or _sha(path) != item["artifact_sha256"]:
                raise ValueError(f"Artifact does not match manifest: {method}")
        if _sha(files["explicit"]) != source["source_sha256"]:
            raise ValueError("Explicit source differs")
        if hashlib.sha256(gzip.decompress(files["gzip"].read_bytes())).hexdigest() != source["source_sha256"]:
            raise ValueError("gzip reconstruction differs")
        artifact_check.update(hashes_match_manifest=True, gzip_independent_roundtrip=True)
        # .crtc needs a compatible native decoder, which is not part of this independent Python script.
        # Historical transfer-test verification records are examined below, not passed off as decoding here.
    times = defaultdict(list)
    decode = defaultdict(list)
    seen = defaultdict(int)
    for row in trial_rows:
        method, scenario = row["method"], row["scenario"]
        if method not in METHODS or not scenario:
            raise ValueError("Unknown method or scenario")
        if row["exact_original_sha256_verified"].lower() != "true":
            raise ValueError("Non-verified transfer found")
        if int(row["source_bytes"]) != source["source_bytes"]:
            raise ValueError("Source-byte mismatch in trial")
        if int(row["artifact_bytes"]) != manifest["variants"][method]["artifact_bytes"]:
            raise ValueError("Representation-byte mismatch in trial")
        key = (scenario, method)
        times[key].append(_safe_float(row["total_wall_ms"], "total_wall_ms"))
        decode[key].append(_safe_float(row["reconstruction_verified_ms"], "reconstruction_verified_ms"))
        seen[key] += 1
    scenario_lookup = {x["profile"]["name"]: x for x in summary["scenarios"]}
    if set(scenario_lookup) != {k[0] for k in times}:
        raise ValueError("Scenario coverage mismatch")
    medians = {}
    for scenario, info in scenario_lookup.items():
        medians[scenario] = {}
        for method in METHODS:
            key = (scenario, method)
            if seen[key] != info["rounds"]:
                raise ValueError("Unbalanced / missing trial observations")
            median = statistics.median(times[key])
            if abs(median - info["median_wall_ms"][method]) > .01:
                raise ValueError("CSV timing data differs from summary")
            medians[scenario][method] = {"wall_ms": round(median, 3),
                                          "reconstruction_verified_ms": round(statistics.median(decode[key]), 3),
                                          "artifact_bytes": manifest["variants"][method]["artifact_bytes"],
                                          "verified_trials": seen[key]}
    return {
        "source_sha256": source["source_sha256"], "source_bytes": source["source_bytes"],
        "trial_count": len(trial_rows), "scope": summary["scope"], "medians": medians,
        "artifact_checks": artifact_check,
        "limits": ["localhost application-layer shaping, not WAN evidence",
                   "single structured TSV source, not general codec superiority",
                   "measured reconstruction+verification wall time is used as an imperfect CPU-cost proxy",
                   "pre-encoding, storage, distribution infrastructure, and integration costs not measured",
                   "no independent CRTC decoder in this buyer script; .crtc exactness relies on benchmark verification records",
                   "Xet LZ4 / BG4-LZ4 are not measured in this evidence set",
                   "synthetic workloads and cost rates are not real customers or quotes; $4.99 one-time price and optional $0.99/month update offer are proposed, not published",
                   "trusted benchmark manifest is not an authenticated production package"],
    }


def evaluate_mandate(evidence, mandate):
    """Minimize stated *hypothetical* cost subject to explicit SLA and authorization constraints."""
    name = str(mandate["name"])
    profile = mandate["profile"]
    if profile not in evidence["medians"]:
        raise ValueError(f"Unsupported profile {profile}")
    copies = _safe_float(mandate["transfers_per_month"], "transfers_per_month")
    if not copies.is_integer():
        raise ValueError("transfers_per_month must be integer")
    egress = _safe_float(mandate["egress_usd_per_gb"], "egress_usd_per_gb")
    cpu = _safe_float(mandate["cpu_usd_per_hour"], "cpu_usd_per_hour")
    budget = _safe_float(mandate["monthly_spend_authority_usd"], "monthly_spend_authority_usd")
    sla = _safe_float(mandate["max_verified_transfer_ms"], "max_verified_transfer_ms")
    # Perpetual purchase is not a recurring license. Amortization is a buyer
    # analysis assumption over an explicit horizon, not a subscription.
    horizon = _safe_float(mandate["evaluation_horizon_months"], "evaluation_horizon_months")
    if horizon <= 0 or not horizon.is_integer():
        raise ValueError("evaluation_horizon_months must be a positive integer")
    prices = mandate["one_time_purchase_prices_usd"]
    if set(prices) != set(METHODS):
        raise ValueError("All alternatives need explicit one-time purchase prices")
    upfront_authority = _safe_float(mandate["upfront_purchase_authority_usd"], "upfront_purchase_authority_usd")
    subscription = _safe_float(mandate.get("optional_update_subscription_usd_per_month", 0),
                               "optional_update_subscription_usd_per_month")
    subscribe = mandate.get("opt_in_updates", False)
    if type(subscribe) is not bool:
        raise ValueError("opt_in_updates must be a boolean")
    fixed = mandate.get("integration_cost_usd_per_month", {})
    choices = []
    for method in METHODS:
        metrics = evidence["medians"][profile][method]
        purchase = _safe_float(prices[method], f"{method} purchase")
        setup = _safe_float(fixed.get(method, 0), f"{method} integration")
        updates = subscription if method == "constructive" and subscribe else 0.0
        network_cost = metrics["artifact_bytes"] * copies / 1e9 * egress
        reconstruction_cost = metrics["reconstruction_verified_ms"] * copies / 3_600_000 * cpu
        monthly_cost = network_cost + reconstruction_cost + purchase / horizon + updates + setup
        in_sla = metrics["wall_ms"] <= sla
        in_upfront_budget = purchase <= upfront_authority
        in_monthly_budget = updates + setup <= budget
        choices.append({"method": method, "eligible": in_sla and in_upfront_budget and in_monthly_budget,
                        "measured_median_wall_ms": metrics["wall_ms"],
                        "source_verified_trials": metrics["verified_trials"],
                        "one_time_purchase_usd": round(purchase, 6),
                        "evaluation_horizon_months": int(horizon),
                        "monthly_amortized_purchase_usd": round(purchase / horizon, 6),
                        "updates_opted_in": bool(method == "constructive" and subscribe),
                        "monthly_optional_updates_usd": round(updates, 6),
                        "perpetual_right_to_purchased_version": method == "constructive",
                        "monthly_network_usd": round(network_cost, 6),
                        "monthly_cpu_proxy_usd": round(reconstruction_cost, 6),
                        "monthly_integration_usd": round(setup, 6),
                        "total_estimated_monthly_usd": round(monthly_cost, 6),
                        "disqualification": (["latency_sla"] if not in_sla else []) +
                                            (["upfront_purchase_authority"] if not in_upfront_budget else []) +
                                            (["monthly_spend_authority"] if not in_monthly_budget else [])})
    feasible = [c for c in choices if c["eligible"]]
    selected = min(feasible, key=lambda c: (c["total_estimated_monthly_usd"], c["measured_median_wall_ms"], c["method"])) if feasible else None
    gzip_choice = next(c for c in choices if c["method"] == "gzip")
    return {
        "mandate": name, "profile": profile, "simulated": True,
        "selected": selected["method"] if selected else None,
        "decision": "SIMULATED_SELECT" if selected else "NO_ELIGIBLE_OPTION",
        "transaction_occurred": False, "actual_revenue_usd": 0,
        "selected_cost_usd": selected["total_estimated_monthly_usd"] if selected else None,
        "estimated_delta_vs_gzip_usd": (round(gzip_choice["total_estimated_monthly_usd"] - selected["total_estimated_monthly_usd"], 6)
                                            if selected else None),
        "buyer_authorization": "synthetic test mandate; no spending authority in real world",
        "candidates": choices,
    }


def run(summary, trials, artifact_dir, mandates):
    evidence = load_evidence(Path(summary), Path(trials), Path(artifact_dir) if artifact_dir else None)
    mandate_set = json.loads(Path(mandates).read_text(encoding="utf-8"))
    decisions = [evaluate_mandate(evidence, m) for m in mandate_set["mandates"]]
    return {"schema": "good-economy-agent.buyer-precedent.v1", "experiment": "independent_buyer_simulation",
            "simulation_only": True, "outside_payment_authority": False,
            "actual_revenue_usd": 0, "agent_no_preference_for_constructivert": True,
            "selection_rule": "minimize monthly cost over declared amortization horizon among SLA-eligible choices passing upfront and recurring authorization separately",
            "evidence": evidence, "decisions": decisions,
            "unmeasured_competitors": ["HF Xet None", "HF Xet LZ4", "HF Xet BG4-LZ4"],
            "real_purchase_status": "not performed; proposed pricing not yet published; buyer authority and workload suitability unverified"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--summary", required=True)
    p.add_argument("--trials", required=True)
    p.add_argument("--artifacts-dir")
    p.add_argument("--mandates", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    report = run(a.summary, a.trials, a.artifacts_dir, a.mandates)
    Path(a.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for d in report["decisions"]:
        print(f"{d['mandate']}: {d['decision']} {d['selected']} ; real purchases=0")


if __name__ == "__main__":
    main()