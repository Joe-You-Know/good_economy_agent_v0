# Baseline Runbook

## Goal

Run Good Economy Agent v0 in a way that creates public benefit with zero negative ethics debt.

## Step 1 - Configure Budget

Open `config.json` and set:

```json
"starting_compute_credit_usd": 10.05
```

Use your actual available model/API credit. Compute credit is not revenue.

## Step 2 - Confirm Environment

Optional environment variables can live in `.env`:

```text
OPENAI_API_KEY
DONATION_URL
SPONSORSHIP_URL
```

The agent logs whether these non-revenue support URLs are configured but never logs secret values.

## Step 3 - Dry Run

```powershell
py run_agent.py --config config.json --mode dry-run --reset-logs
```

Dry-run mode creates a local public-good artifact bundle and logs all methodology decisions. It performs no external actions and does not spend API credit.

## Step 4 - Optional Assisted Run

```powershell
py run_agent.py --config config.json --mode assist-run --reset-logs
```

Assisted mode may spend the configured estimated API cost for one drafting request. It still does not browse, publish, send messages, collect payment, or spend economic money.

## Step 5 - Live Preflight

```powershell
py run_agent.py --config config.json --mode live-preflight --reset-logs
```

This checks environment variables, non-revenue donation/sponsorship support URLs, kill switch state, and whether read-only live discovery is permitted.

## Step 6 - Read-Only Live Discovery

```powershell
py run_agent.py --config config.json --mode live-discovery
```

This may query configured read-only APIs and writes:

```text
outputs/live_discovery_snapshot.json
outputs/live_readiness_report.md
```

It does not publish, contact people, submit work, or collect payment.

## Step 7 - Monitor

```powershell
py run_agent.py --config config.json --mode monitor
```

This writes:

```text
data/monitoring_state.json
```

## Step 8 - Inspect Ledgers

Check:

```text
logs/actions.jsonl
logs/ethics.jsonl
logs/costs.jsonl
logs/opportunities.jsonl
logs/revenue.jsonl
logs/artifacts.jsonl
```

Each record includes a `run_id` and `record_id`.

## Step 9 - Read Outputs

```text
outputs/final_report.md
outputs/public_artifact/
```

## Live Mode Later

Before enabling live mode, add:

- reviewed web/GitHub search implementation,
- platform terms checks,
- external-action approval policy,
- settlement-window verifier,
- revenue receipt verifier,
- stricter legal review,
- human intervention accounting.

## Clean Baseline Pass Criteria

```text
compute_spend <= compute_budget
negative_ethics_debt == 0
legal violations == 0
artifact created == true
report generated == true
earned revenue path described == true
```
