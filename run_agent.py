import argparse
import json
import os
from pathlib import Path

from agent.artifact_builder import ArtifactBuilder
from agent.config import environment_capabilities, load_env_file, load_json_config, public_support_links
from agent.env_manager import EnvManager
from agent.ethics_gate import EthicsGate
from agent.ledger import JsonlLedger
from agent.live_discovery import LiveDiscovery
from agent.live_readiness import LiveReadiness
from agent.monitor import Monitor
from agent.openai_planner import OpenAIPlanner
from agent.opportunity_finder import OpportunityFinder
from agent.opportunity_score import explain_opportunity_score
from agent.report_writer import ReportWriter
from agent.revenue_tracker import RevenueTracker
from agent.supervised_work import SupervisedWorkRunner
from agent.wallet import ComputeWallet, EconomicWallet


def run(config_path: Path, mode: str, reset_logs: bool = False, revenue_event_path: Path = None):
    root = Path(__file__).resolve().parent
    config_path = _resolve_path(root, config_path)
    config = load_json_config(config_path)
    load_env_file(root / ".env")

    log_dir = root / "logs"
    output_dir = root / "outputs"
    ledger = JsonlLedger(log_dir, reset=reset_logs)

    if mode == "live-preflight":
        ledger.append("actions", {
            "action": "run_started",
            "mode": mode,
            "experiment_name": config["experiment_name"],
            "config_path": str(config_path),
            "environment_capabilities": environment_capabilities(),
        })
        return _run_live_preflight(root, output_dir, config, ledger)
    if mode == "live-discovery":
        ledger.append("actions", {
            "action": "run_started",
            "mode": mode,
            "experiment_name": config["experiment_name"],
            "config_path": str(config_path),
            "environment_capabilities": environment_capabilities(),
        })
        return _run_live_discovery(root, output_dir, config, ledger)
    if mode == "monitor":
        ledger.append("actions", {
            "action": "run_started",
            "mode": mode,
            "experiment_name": config["experiment_name"],
            "config_path": str(config_path),
            "environment_capabilities": environment_capabilities(),
        })
        return _run_monitor(root, config, ledger)
    if mode == "env-bootstrap":
        ledger.append("actions", {
            "action": "run_started",
            "mode": mode,
            "experiment_name": config["experiment_name"],
            "config_path": str(config_path),
            "environment_capabilities": environment_capabilities(),
        })
        return _run_env_bootstrap(root, output_dir, ledger)
    if mode == "env-sync":
        ledger.append("actions", {
            "action": "run_started",
            "mode": mode,
            "experiment_name": config["experiment_name"],
            "config_path": str(config_path),
            "environment_capabilities": environment_capabilities(),
        })
        return _run_env_sync(root, output_dir, ledger)
    if mode == "env-report":
        ledger.append("actions", {
            "action": "run_started",
            "mode": mode,
            "experiment_name": config["experiment_name"],
            "config_path": str(config_path),
            "environment_capabilities": environment_capabilities(),
        })
        return _run_env_report(root, output_dir, ledger)
    if mode == "revenue-verify":
        ledger.append("actions", {
            "action": "run_started",
            "mode": mode,
            "experiment_name": config["experiment_name"],
            "config_path": str(config_path),
            "environment_capabilities": environment_capabilities(),
        })
        return _run_revenue_verify(root, output_dir, ledger, revenue_event_path)
    if mode == "supervised-work":
        ledger.append("actions", {
            "action": "run_started",
            "mode": mode,
            "experiment_name": config["experiment_name"],
            "config_path": str(config_path),
            "environment_capabilities": environment_capabilities(),
        })
        return _run_supervised_work(root, config, ledger)

    compute_wallet = ComputeWallet(
        starting_credit_usd=float(config["starting_compute_credit_usd"]),
        hard_stop_remaining_usd=float(config["hard_stop_compute_remaining_usd"]),
        max_single_charge_usd=float(config["max_single_call_usd"]),
    )
    economic_wallet = EconomicWallet(
        starting_cash_usd=float(config["starting_economic_cash_usd"])
    )
    revenue_tracker = RevenueTracker()

    env_capabilities = environment_capabilities()
    ledger.append("actions", {
        "action": "run_started",
        "mode": mode,
        "experiment_name": config["experiment_name"],
        "config_path": str(config_path),
        "starting_compute_credit_usd": config["starting_compute_credit_usd"],
        "starting_economic_cash_usd": config["starting_economic_cash_usd"],
        "environment_capabilities": env_capabilities,
    })

    methodology_charge = compute_wallet.charge(0.01, "baseline methodology, scoring, and report accounting")
    ledger.append("costs", methodology_charge)

    finder = OpportunityFinder(root / "data" / "opportunity_examples.json")
    opportunities = finder.load_seed_opportunities()

    scored = []
    for opp in opportunities:
        explanation = explain_opportunity_score(opp, config)
        record = opp.to_dict()
        record["score"] = explanation["score"]
        record["score_explanation"] = explanation
        ledger.append("opportunities", record)
        scored.append((explanation["score"], explanation, opp))

    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best_explanation, best = scored[0]

    selection_record = ledger.append("actions", {
        "action": "selected_opportunity",
        "opportunity_id": best.id,
        "title": best.title,
        "score": best_score,
        "selection_reason": (
            "highest score under public-benefit, feasibility, verification, "
            "cost, and zero-negative-ethics criteria"
        ),
    })

    ethics_gate = EthicsGate(config)
    ethics_decision = ethics_gate.evaluate_action({
        "action_type": "build_public_good_artifact",
        "category": best.category,
        "opportunity_id": best.id,
        "risk_tags": best.risk_tags,
        "requires_cold_outreach": False,
        "requires_paid_tool": False,
        "requires_personal_network": False,
        "external_action": False,
        "collects_personal_data": False,
        "explicit_consent": True,
        "makes_professional_claims": False,
        "public_benefit_score": best.public_benefit_score,
        "evidence_strength": best.verification_strength,
        "truth_claims": ["artifact is free", "earned revenue path is optional", "support is not revenue", "limits are disclosed"],
        "consent_mechanism": "voluntary opt-in use and voluntary opt-in support only",
        "revenue_path": True,
        "reversibility": "local artifact can be edited, corrected, withdrawn, or replaced",
        "rejects_harmful_shortcuts": True,
    })
    ledger.append("ethics", ethics_decision.to_dict())

    if not ethics_decision.allowed:
        ledger.append("actions", {
            "action": "halted_by_ethics_gate",
            "opportunity_id": best.id,
            "reasons": ethics_decision.reasons,
        })
        raise SystemExit("Ethics gate blocked the selected action.")

    ai_draft = _maybe_get_openai_assist(
        root=root,
        mode=mode,
        config=config,
        opportunity=best,
        compute_wallet=compute_wallet,
        ledger=ledger,
    )

    builder = ArtifactBuilder(
        output_dir,
        license_text=config["artifact_license"],
        support_links=public_support_links(),
    )
    artifact = builder.build(best, ai_draft=ai_draft)
    artifact_record = ledger.append("artifacts", artifact.to_dict())

    ledger.append("actions", {
        "action": "artifact_bundle_created",
        "opportunity_id": best.id,
        "artifact_record_id": artifact_record["record_id"],
        "files": artifact.files,
    })

    no_revenue = revenue_tracker.no_revenue_event(
        "Dry-run and assist-run modes describe an earned revenue path but do not collect external revenue."
    )
    ledger.append("revenue", no_revenue)

    net_liquid = economic_wallet.earned_usd - economic_wallet.spent_usd - compute_wallet.spent_usd

    summary = {
        "experiment_name": config["experiment_name"],
        "run_id": ledger.run_id,
        "mode": mode,
        "starting_economic_cash_usd": economic_wallet.starting_cash_usd,
        "starting_compute_credit_usd": compute_wallet.starting_credit_usd,
        "compute_spent_usd": compute_wallet.spent_usd,
        "compute_remaining_usd": compute_wallet.remaining_usd,
        "externally_earned_revenue_usd": economic_wallet.earned_usd,
        "economic_spent_usd": economic_wallet.spent_usd,
        "net_liquid_score_usd": net_liquid,
        "selected_opportunity_id": best.id,
        "selected_opportunity_title": best.title,
        "selected_opportunity_category": best.category,
        "selected_opportunity_score": best_score,
        "selected_score_explanation": best_explanation,
        "artifact": artifact.to_dict(),
        "negative_ethics_debt": ethics_decision.negative_debt,
        "positive_ethics_score": ethics_decision.positive_score,
        "ethics_reasons": ethics_decision.reasons,
        "baseline_clean_ethics_pass": ethics_decision.negative_debt == 0.0,
        "environment_capabilities": env_capabilities,
        "revenue_status": no_revenue["reason"],
        "selection_action_id": selection_record["record_id"],
    }

    report_path = ReportWriter(output_dir).write_final_report(summary)

    ledger.append("actions", {
        "action": "run_completed",
        "final_report": str(report_path),
        "net_liquid_score_usd": round(net_liquid, 6),
        "negative_ethics_debt": ethics_decision.negative_debt,
        "positive_ethics_score": ethics_decision.positive_score,
    })

    print("Run complete.")
    print(f"Run ID: {ledger.run_id}")
    print(f"Final report: {report_path}")
    print(f"Artifact path: {artifact.path}")
    print(f"Net liquid score: ${net_liquid:.4f}")
    print(f"Negative ethics debt: {ethics_decision.negative_debt}")


def _maybe_get_openai_assist(
    root: Path,
    mode: str,
    config,
    opportunity,
    compute_wallet: ComputeWallet,
    ledger: JsonlLedger,
) -> str:
    if mode != "assist-run":
        ledger.append("actions", {
            "action": "openai_assist_not_used",
            "reason": "mode is dry-run",
        })
        return ""

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        ledger.append("actions", {
            "action": "openai_assist_skipped",
            "reason": "OPENAI_API_KEY is not configured",
        })
        return ""

    estimated_cost = float(config["openai_assist_estimated_call_usd"])
    charge = compute_wallet.charge(estimated_cost, "optional OpenAI-assisted artifact drafting")
    ledger.append("costs", charge)

    methodology = (root / "METHODOLOGY.md").read_text(encoding="utf-8")
    planner = OpenAIPlanner(
        api_key=api_key,
        model=config["openai_assist_model"],
        timeout_seconds=int(config["openai_assist_timeout_seconds"]),
    )
    result = planner.draft_public_artifact_notes(
        opportunity,
        methodology,
        max_output_tokens=int(config["openai_assist_max_output_tokens"]),
    )

    if result["ok"]:
        ledger.append("actions", {
            "action": "openai_assist_completed",
            "model": result.get("model"),
            "output_chars": len(result["text"]),
            "note": "Generated text is stored only in the local artifact bundle for review.",
        })
        return result["text"]

    ledger.append("actions", {
        "action": "openai_assist_failed",
        "error": result["error"],
        "fallback": "deterministic artifact builder",
    })
    return ""


def _resolve_path(root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    candidate = Path.cwd() / path
    if candidate.exists():
        return candidate
    return root / path


def _run_live_preflight(root: Path, output_dir: Path, config, ledger: JsonlLedger):
    readiness = LiveReadiness(root, config)
    report = readiness.evaluate()
    report_path = readiness.write_report(output_dir, report)
    ledger.append("actions", {
        "action": "live_preflight_completed",
        "ready_for_read_only_live_discovery": report["ready_for_read_only_live_discovery"],
        "ready_for_live_write_actions": report["ready_for_live_write_actions"],
        "blockers": report["blockers"],
        "warnings": report["warnings"],
        "report_path": str(report_path),
    })
    print("Live preflight complete.")
    print(f"Run ID: {ledger.run_id}")
    print(f"Read-only live discovery ready: {report['ready_for_read_only_live_discovery']}")
    print(f"Live write actions ready: {report['ready_for_live_write_actions']}")
    print(f"Report: {report_path}")
    return report


def _run_live_discovery(root: Path, output_dir: Path, config, ledger: JsonlLedger):
    readiness_runner = LiveReadiness(root, config)
    readiness = readiness_runner.evaluate()
    readiness_path = readiness_runner.write_report(output_dir, readiness)
    ledger.append("actions", {
        "action": "live_discovery_preflight",
        "ready_for_read_only_live_discovery": readiness["ready_for_read_only_live_discovery"],
        "blockers": readiness["blockers"],
        "warnings": readiness["warnings"],
        "report_path": str(readiness_path),
    })
    if not readiness["ready_for_read_only_live_discovery"]:
        raise SystemExit("Live discovery blocked by preflight. See outputs/live_readiness_report.md.")

    discovery = LiveDiscovery(root, config, ledger).run()
    print("Live discovery complete.")
    print(f"Run ID: {ledger.run_id}")
    print(f"Snapshot: {root / 'outputs' / 'live_discovery_snapshot.json'}")
    return discovery


def _run_monitor(root: Path, config, ledger: JsonlLedger):
    snapshot = Monitor(root, config).snapshot()
    ledger.append("actions", {
        "action": "monitor_snapshot_written",
        "kill_switch_triggered": snapshot["kill_switch"]["triggered"],
        "ledger_counts": snapshot["ledger_counts"],
    })
    print("Monitor snapshot complete.")
    print(f"Run ID: {ledger.run_id}")
    print(f"Kill switch triggered: {snapshot['kill_switch']['triggered']}")
    print(f"Monitoring state: {root / config['monitoring_state_path']}")
    return snapshot


def _run_env_bootstrap(root: Path, output_dir: Path, ledger: JsonlLedger):
    manager = EnvManager(root)
    result = manager.bootstrap()
    report_path = manager.write_report(output_dir)
    ledger.append("actions", {
        "action": "env_bootstrap_completed",
        "env_path": result["env_path"],
        "added_keys": result["added"],
        "report_path": str(report_path),
        "secret_values_logged": False,
    })
    print("Environment bootstrap complete.")
    print(f"Added keys: {len(result['added'])}")
    print(f"Report: {report_path}")
    return result


def _run_env_sync(root: Path, output_dir: Path, ledger: JsonlLedger):
    manager = EnvManager(root)
    result = manager.sync_from_process()
    report_path = manager.write_report(output_dir)
    ledger.append("actions", {
        "action": "env_sync_completed",
        "env_path": result["env_path"],
        "changed_keys": result["changed"],
        "skipped_count": len(result["skipped"]),
        "report_path": str(report_path),
        "secret_values_logged": False,
    })
    print("Environment sync complete.")
    print(f"Changed keys: {len(result['changed'])}")
    print(f"Report: {report_path}")
    return result


def _run_env_report(root: Path, output_dir: Path, ledger: JsonlLedger):
    manager = EnvManager(root)
    report = manager.report()
    report_path = manager.write_report(output_dir)
    ledger.append("actions", {
        "action": "env_report_completed",
        "missing_keys": report["missing"],
        "invalid_keys": report["invalid"],
        "report_path": str(report_path),
        "secret_values_logged": False,
    })
    print("Environment report complete.")
    print(f"Missing keys: {len(report['missing'])}")
    print(f"Invalid keys: {len(report['invalid'])}")
    print(f"Report: {report_path}")
    return report


def _run_revenue_verify(root: Path, output_dir: Path, ledger: JsonlLedger, revenue_event_path: Path = None):
    if revenue_event_path is None:
        raise SystemExit("revenue-verify requires --revenue-event path/to/event.json")

    event_path = _resolve_path(root, Path(revenue_event_path))
    if not event_path.exists():
        raise SystemExit(f"Revenue event file does not exist: {event_path}")

    event = json.loads(event_path.read_text(encoding="utf-8"))
    if not isinstance(event, dict):
        raise SystemExit("Revenue event file must contain a JSON object.")

    tracker = RevenueTracker()
    result = tracker.validate_revenue_event(event)
    ledger.append("revenue", result)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "revenue_validation_report.md"
    report_path.write_text(_render_revenue_validation_report(event_path, result), encoding="utf-8")
    ledger.append("actions", {
        "action": "revenue_event_validated",
        "revenue_event_path": str(event_path),
        "valid": result["valid"],
        "reason": result["reason"],
        "report_path": str(report_path),
    })

    print("Revenue verification complete.")
    print(f"Valid earned revenue: {result['valid']}")
    print(f"Reason: {result['reason']}")
    print(f"Report: {report_path}")
    return result


def _run_supervised_work(root: Path, config, ledger: JsonlLedger):
    decision = SupervisedWorkRunner(root, config, ledger).run()
    print("Supervised work decision complete.")
    print(f"Status: {decision['status']}")
    selected = decision.get("selected_candidate") or {}
    if selected:
        print(f"Selected: {selected.get('title')}")
        print(f"Source: {selected.get('source_url')}")
    print(f"Decision: {root / 'outputs' / 'supervised_work_decision.md'}")
    return decision


def _render_revenue_validation_report(event_path: Path, result) -> str:
    event = result.get("event", {})
    evidence = event.get("evidence", [])
    if isinstance(evidence, dict):
        evidence_lines = "\n".join(f"- {key}: {value}" for key, value in evidence.items())
    elif isinstance(evidence, list):
        evidence_lines = "\n".join(f"- {item}" for item in evidence)
    else:
        evidence_lines = f"- {evidence}" if evidence else "- none"

    return f"""# Earned Revenue Validation Report

Event file: `{event_path}`

## Result

- Valid earned revenue: {result["valid"]}
- Reason: {result["reason"]}
- Amount: ${float(event.get("amount_usd", 0.0)):.2f}
- Income type: {event.get("income_type", "")}
- Classification: {event.get("classification", "")}
- Source: {event.get("source", "")}
- Caused by action id: {event.get("caused_by_action_id", "")}

## Evidence

{evidence_lines}

## Boundary

Donation, patronage, sponsorship, grant, and gift inflows are not revenue. A valid event must be earned income from a real value exchange, traceable, consented, net of fees, and tied to logged agent work.
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Good Economy Agent v0.")
    parser.add_argument("--config", default="config.json", help="Path to config JSON.")
    parser.add_argument(
        "--mode",
        default="dry-run",
        choices=[
            "dry-run",
            "assist-run",
            "live-preflight",
            "live-discovery",
            "monitor",
            "env-bootstrap",
            "env-sync",
            "env-report",
            "revenue-verify",
            "supervised-work",
        ],
        help="Execution mode.",
    )
    parser.add_argument("--reset-logs", action="store_true", help="Clear known v0 ledgers before the run.")
    parser.add_argument("--revenue-event", default="", help="Path to a JSON event for revenue-verify mode.")
    args = parser.parse_args()

    run(
        Path(args.config),
        args.mode,
        reset_logs=args.reset_logs,
        revenue_event_path=Path(args.revenue_event) if args.revenue_event else None,
    )
