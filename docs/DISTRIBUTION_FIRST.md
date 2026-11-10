# Distribution-first economic experiments

## Question

Can an independently useful, transparent implementation reach users, earn voluntary payments, and support household stability without first establishing a personal client list?

This is a **different experiment** from securing bounties. The repository's original earned-income finder is retained as a comparison baseline, not treated as the primary distribution strategy.

## Two independent ledgers

1. **Economic:** independently settled revenue minus all operational and transaction costs, with grants, gifts, and donations tracked as support rather than earned revenue.
2. **Adaptive benefit:** reproducible observed improvement in a participant's capacity to understand or act, together with adverse effects and uncertainty. Benefits cannot cancel harms.

No measurement of adoption, net revenue, or benefit is inferred from a successful code run.

## Target sequence

1. **Evidence:** select an existing working capability. Separate measured behavior from hypotheses. Publish test inputs, outputs, environment and limitations when disclosure is safe.
2. **Comparison:** evaluate against the strongest ordinary alternative under equivalent conditions. Check correctness first, then wall time, memory, setup time and operational burden.
3. **Distribution:** make a self-service public package/demo available where its intended users already search. Track actual impressions, installs, activations and repeat use if authorized and privacy-preserving.
4. **Commercial path:** optional paid convenience/hosting/integration, transparent methodology, no hidden fees. Keep original research accessible to independent inspection.
5. **Verification:** count only real authorized transactions supported by a receipt; measure net revenue and user benefit separately.

## Initial candidate: Constructive Runtime

The portfolio describes local ConstructiveRT diagnostic tooling, while earlier experiments also explored repeated-computation reuse/adaptive promotion. These should **not** be conflated into one measured product. Locate and audit the actual source and tests for whichever implementation is chosen before release.

Possible differentiators to test—not established claims:
- Correctness-preserving automatic detection of reusable computation
- A report-first, opt-in optimization pathway for existing scripts
- Dependency-aware invalidation versus basic memoization
- Lower total effort to adopt safely

Baseline comparators should include Python `functools.lru_cache`, `functools.cache`, and `joblib.Memory` where their semantics apply.

## Discovery before promotion

Every candidate record should include:
- A specific recurring problem and evidence users experience it
- Existing alternatives, including free ones
- A runnable independent comparison
- A real distribution entry point (package index, marketplace or search channel)
- Adoptability/permissions and data/privacy risks
- A credible voluntary transaction mechanism
- Falsification conditions (what result would make us stop)

Reject ideas based only on projected attention, unverified speedups, or a hypothetical buyer.

## Current automation boundary

`.github/workflows/economy-safe-audit.yml` runs offline unit tests and an offline dry-run on pull requests or manual dispatch. Its **optional** manual switch runs the existing read-only discovery process and stores the results as restricted GitHub Actions artifacts for review.

This workflow does not schedule itself, publish software, submit pull requests to third parties, contact people, handle payment information, or verify a sale. Those changes need explicit separate authorization and audit. Its success is infrastructure readiness, **not** evidence of economic progress.

## Next implementation gate

Create an independently reproducible product benchmark from reviewed source, then produce a minimal public self-service demo/package **only after** reviewing licensing, proprietary materials, secrets, and released claims. A passing benchmark and opt-in usage are prerequisites for attempting payment integration.
