from pathlib import Path
from typing import Any, Dict, Iterable


class ReportWriter:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_final_report(self, summary: Dict[str, Any]) -> Path:
        path = self.output_dir / "final_report.md"
        artifact = summary["artifact"]
        score = summary["selected_score_explanation"]

        report = f"""# Good Economy Agent v0 - Final Report

## Experiment

- Name: {summary["experiment_name"]}
- Run ID: `{summary["run_id"]}`
- Mode: {summary["mode"]}

## Wallets

- Starting economic cash: ${summary["starting_economic_cash_usd"]:.2f}
- Starting compute credit: ${summary["starting_compute_credit_usd"]:.2f}
- Compute spent: ${summary["compute_spent_usd"]:.4f}
- Compute remaining: ${summary["compute_remaining_usd"]:.4f}
- Externally earned revenue: ${summary["externally_earned_revenue_usd"]:.2f}
- Economic spend: ${summary["economic_spent_usd"]:.2f}
- Net liquid score: ${summary["net_liquid_score_usd"]:.4f}

## Selected Opportunity

- ID: `{summary["selected_opportunity_id"]}`
- Title: {summary["selected_opportunity_title"]}
- Category: {summary["selected_opportunity_category"]}
- Score: {summary["selected_opportunity_score"]}
- Gross value component: {score["gross_value"]}
- Cost penalty: {score["cost_penalty"]}
- Safety penalty: {score["safety_penalty"]}
- Penalty reasons: {_inline_list(score["penalty_reasons"])}

## Artifact Created

- Title: {artifact["title"]}
- Primary path: `{artifact["path"]}`
- Files: {_inline_list(artifact["files"])}
- Public benefit claim: {artifact["public_benefit_claim"]}
- Revenue path: {artifact["revenue_path"]}
- Content source: {artifact["content_source"]}
- License: {artifact["license"]}

## Ethics

- Negative ethics debt: {summary["negative_ethics_debt"]}
- Positive ethics score: {summary["positive_ethics_score"]}
- Baseline clean ethics pass: {summary["baseline_clean_ethics_pass"]}
- Ethics decision reasons: {_inline_list(summary["ethics_reasons"])}

## Environment Capabilities

{_capability_lines(summary["environment_capabilities"])}

## Revenue Validation

- External revenue recorded: ${summary["externally_earned_revenue_usd"]:.2f}
- Revenue ledger status: {summary["revenue_status"]}

## Legal and Safety Notes

This run performed no cold outreach, no scraping, no payment action, no ad
activity, no affiliate activity, no faucet activity, and no customer contact.
Any future external action must pass the ethics gate and platform/legal review.

## Baseline Result

```text
negative_ethics_debt = {summary["negative_ethics_debt"]}
compute_spent = ${summary["compute_spent_usd"]:.4f}
artifact_created = true
revenue_path_described = true
```

The clean-baseline result is {summary["baseline_clean_ethics_pass"]}.

## Next Safe Step

Run `assist-run` only when you intentionally want to spend a small, logged
amount of compute credit on model-assisted drafting. Live publication, outbound
messages, or payment collection should be separate reviewed modes.
"""
        path.write_text(report, encoding="utf-8")
        return path


def _inline_list(values: Iterable[Any]) -> str:
    values = list(values or [])
    if not values:
        return "none"
    return "; ".join(str(value) for value in values)


def _capability_lines(capabilities: Iterable[Dict[str, Any]]) -> str:
    lines = []
    for item in capabilities:
        status = "configured" if item.get("configured") else "not configured"
        lines.append(f"- {item.get('name')}: {status} ({item.get('classification')})")
    return "\n".join(lines) if lines else "- none inspected"
