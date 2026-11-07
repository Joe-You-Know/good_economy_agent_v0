# GitHub Workflow and Reconciliation

Reviewed: 2026-11-07.

Canonical private repository:
https://github.com/Joe-You-Know/good_economy_agent_v0

## Working From GitHub

Use issues for objectives and missing inputs, pull requests for reviewed source,
and Actions for repeatable execution and downloadable evidence. Start from the
latest remote branch. A chat transcript or local output directory is supporting
context, not a substitute for committed source and recorded run results.

PR #1, `automation/safe-economy-audit-2026-11`, is the reconciliation branch.
It combines the remote audit/distribution work and the recovered local work.
The default branch remains unchanged until the owner reviews and merges the PR.

```text
python -m unittest discover -s tests
python run_agent.py --config config.json --mode dry-run --reset-logs
python -m tools.observable_ecc_bench --outdir outputs/research_smoke
```

The workflow runs these checks on Linux and Windows for PR changes. Manual
read-only discovery runs once on Linux when explicitly selected after the
workflow has reached the default branch. Reports are Actions artifacts with
14-day retention; preserve selected non-sensitive evidence with an issue or PR
before it expires. No recurring schedule is configured.

## Reconciliation Inventory

| Area | Before this reconciliation | Disposition |
|---|---|---|
| GitHub main | `86be067`, June 16 | Kept as the review base |
| Local main | `955a506`, three commits ahead | All three commits merged into the reconciliation branch |
| Remote-only work | Audit workflow and distribution-first plan in PR #1 | Retained |
| Local-only course work | Course/Udemy builders, configurations, data, docs, tests | Added to the private PR |
| Local-only research | Observable ECC, qday, trace, shell and grid tools and tests | Added as existing research source |
| Local outputs | Ignored ledgers, approvals, generated reports, course bundles | Remain local; selected evidence needs explicit curation |
| Downloaded toolchain | Java installation and archive | Excluded |
| Browser publication helpers | Three additional untracked Payhip scripts | Remain local pending a separate review |
| Runtime Auditor 0.1.0 | Issue #2 describes a cloud-generated archive/wheel | Package source and wheel have not been recovered here |
| Transfer Lab v0.9 | Latest work reported in Economic Stability Strategy | Chat download references found; implementation has not been recovered here |

The original local checkout remains intact at
`D:\GoodEconomyAgent\good_economy_agent_v0`. The isolated reconciliation
checkout is `D:\GoodEconomyAgent\github-first-reconcile`. After merge, use a
clean checkout of GitHub main for new work; the original checkout still holds
uncommitted historical work and private execution state.

## What Was Verified

Before reconciliation, PR #1's commit `d3c4313` had a successful Actions run:
https://github.com/Joe-You-Know/good_economy_agent_v0/actions/runs/42352822156

Its offline tests, dry-run, and artifact upload succeeded; optional discovery
was skipped. This verifies that commit only. Check the latest PR head's run for
the reconciled code. The recovered local source passed all 82 unit tests on
Windows before migration.

The reconciled checkout also passed all 82 unit tests, the offline agent dry-run,
and the self-contained F_97 benchmark on 2026-11-07. The benchmark matched the
paper's nine reference rows and reported no recurrence failures. A text scan for
common API-token and private-key formats found no matches in the staged source;
this is a bounded scan, not a complete security audit.

## Current Product Direction

The chat **Economic Stability Strategy**
(`6aedf770-6ac8-83e8-ad56-cd9a68a344d2`) progressed beyond the Auditor described
in issue #2. Its latest reported artifact is
`constructive_runtime_integrated_profiler_v0_9.zip`, linked there as a ChatGPT
download at `/mnt/data/constructive_runtime_integrated_profiler_v0_9.zip`.
The report is linked at `/mnt/data/constructive_transfer_integrated_v0_9/REPORT.md`.
These are references in that chat, not files in this checkout or GitHub.

The chat reports 43 passing tests and a controlled local comparison of Requests,
curl resume, Constructive v0.8 and v0.9. It reports comparable uninterrupted
transfer time for v0.9 versus Requests, but curl resume remained faster during
interruption recovery. Those claims have not been independently rerun here.
The latest requested work there is reducing v0.9 recovery overhead while
preserving source-bound verification. Recover that package before continuing
implementation; do not reconstruct it from the summary and call it the original.

Issue #2's Auditor wheel digest is
`e9ded0cd29c0ab63578df803b21b4eaa462388316590fd63996499f152f81638`.
The issue is a handoff, not an uploaded release. No dedicated Auditor repository
was found in the connected repository inventory during this audit.

## Remaining Work

1. Review and merge the reconciled PR after current-head CI completes.
2. Recover the v0.9 package and evidence from Economic Stability Strategy;
   inventory and verify its source before any import into a product repository.
3. Keep the Auditor release checklist in issue #2 separate from the transfer lab.
4. Supply reviewed qday data and paper/source fixtures for remote research runs.
   The F_97 smoke benchmark is self-contained; larger runs currently take external
   local files as inputs.
5. Decide the recurring audit cadence and state persistence before adding a
   scheduled runner. A local PowerShell loop does not migrate with a GitHub PR;
   rate-limit state and approval requests need durable remote handling.
6. Configure service credentials only for the specific approved workflow that
   needs them. The offline workflow needs none. CourtListener/OpenLaws provider
   setup, payment reconciliation, PyPI, and MCP client validation remain separate.

## Research Evidence Limits

Recovered benchmark tools preserve historical experiments and are not reviewed
release claims. In particular, the synthetic q-only and paired runner currently
uses different generated trials for each mode; it needs matched trials before
reporting paired effect estimates. Its R lane is deterministically derived from
Q, so statistical independence has not been established. The grid's pair-based
collision bound treats dependent pairs as if they supplied independent evidence;
that bound needs statistical review. Full ratio-ledger injectivity and sampled
uniqueness alone do not measure inversion cost. These limitations should travel
with any inherited June benchmark figures.
