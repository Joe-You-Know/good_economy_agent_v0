# Project status — 2026-11-10

This is a dated inventory for the private Good Economy Agent repository. It distinguishes code on `main`, open review branches, and work observed only in a separate local project. It does not claim revenue, deployment, or public release.

## Repository state

| Area | Status and evidence |
| --- | --- |
| Economy Agent `main` | Commit `c806b0f` contains the local asset-income, course, and Udemy preparation lanes plus Payhip helper scripts. The default agent remains local-first; publishing, payments, and outbound economic actions are not enabled by these lanes. |
| GitHub reconciliation | [Draft PR #1](https://github.com/Joe-You-Know/good_economy_agent_v0/pull/1) still holds the offline audit workflow, distribution plan, and recovered research tools. Its head `b710830` passed Linux and Windows Actions on 2026-11-07. Since then, `main` advanced separately to `c806b0f`; re-review its diff and reconcile the overlapping course files before merge. The prior CI result applies to the PR head, not an eventual merge commit. |
| Native v0.22 validation | [Draft PR #4](https://github.com/Joe-You-Know/good_economy_agent_v0/pull/4) is explicitly **CI-only / do not merge**. At head `2d34d3b`, both the isolated CI workflow and independent Windows UCRT64 workflow completed successfully. This validates that branch's configured checks, not v0.23 or full economic/lifecycle parity. |
| Earlier packages | [Issue #2](https://github.com/Joe-You-Know/good_economy_agent_v0/issues/2) tracks the separate Runtime Auditor 0.1.0 release gates. [Issue #3](https://github.com/Joe-You-Know/good_economy_agent_v0/issues/3) tracks recovery and independent reproduction of Transfer Lab v0.9. Neither issue is a release or verified earned-income event. |

## Constructive Runtime Native v0.23

A separate local source tree exists at `C:\ConstructiveRT\constructive_runtime_native_v0_23`. Its README and report describe opt-in timing instrumentation added to the native C++20 downloader while retaining source-bound range manifests, independent whole-file SHA-256, and verified publication. It is not committed to Good Economy Agent `main` or PR #4. The Native runtime is a separate product candidate; source ownership and any public repository or release require their own review.

The local machine-readable Windows result records a successful MSVC x64 configure/build and three passing CTest suites (`native_foundation`, `native_cli_adversarial`, `native_http_adversarial`) on 2026-11-10. This status review inspected `windows-test-results/result.json`; it did not rerun those native tests.

The local 12-round Windows benchmark summary records 36/36 successful transfers of a 12,566,858-byte NumPy wheel, with all six execution orders used twice. Median elapsed times were 1,943.249 ms for curl plus SHA-256, 1,988.228 ms for native full GET, and 1,999.053 ms for native ranges. The differences from curl are about 2.3% and 2.9% for this workload. These are observations from `benchmark-windows-v023/summary.json`, not a demonstrated speed advantage or general WAN ranking. The local CSV and benchmark script are needed for deeper variance and method review; they are not uploaded in this PR. The earlier `REPORT.md` describes a Linux localhost comparison and still says Windows validation is pending; the newer Windows result files supersede that narrow status statement.

## Next recordable steps

1. Reconcile PR #1 with current `main`; preserve its research and workflow work, inspect overlap, and verify CI on the final reviewed head before merging.
2. Keep PR #4 isolated. Review v0.23 source, release manifest, local test logs, and benchmark methodology in the ConstructiveRT project before deciding where to host it. Do not describe the Native runtime as released or faster than curl.
3. Recover the exact Auditor and Transfer Lab packages named in issues #2 and #3 before importing or extending them. Record provenance, digests, tests, and fresh measurements.
4. For the economic experiment, retain the zero-cash start, separate compute and economic wallets, and zero allowed negative ethics debt. Count only externally earned, settled, traceable net revenue. No such revenue is evidenced by this status update.

## Verification for this status update

The existing Economy Agent checkout at `c806b0f` passed `py -m unittest discover -s tests` on Windows on 2026-11-10: 70 tests. The test runner's temporary directory was redirected into the workspace because the default Windows sandbox temp directory was unwritable. No source files were changed and no Native runtime tests or benchmark were rerun here.
