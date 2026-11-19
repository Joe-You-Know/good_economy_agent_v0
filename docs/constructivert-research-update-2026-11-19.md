# ConstructiveRuntime / ConstructiveRT — cumulative engineering and buyer-evidence checkpoint

**Recorded:** 2026-11-19  
**Project scope:** distinct ConstructiveRT transfer/cache runtime, CRTC codecs, and authenticated incremental compilation experiments, tracked as candidate owned engineering assets for Good Economy Agent. This is a **research and decision record**, not a source release, certification, product listing, earned revenue, or an instruction to deploy.

## 1. Provenance and confidence levels

- **Repository-verified earlier checkpoint:** [native v0.23](constructivert-native-v023-2026-11-10.md), with [machine-readable v0.23 summary](constructivert-native-v023-checkpoint.json). Preserve its comparison boundaries.
- **Locally supplied benchmark evidence:** CRT v1.4.9 `crossover_windows.json`, run on Windows with Clang, shared in the research conversation; the aggregate facts below are transcribed from its reported summary. **The full 6,302-line JSON is not committed to this repository**; preserve it separately as the source of individual paired samples and revision roots. The result should not be represented as an independently rerun GitHub CI experiment.
- **Earlier research reports and plans:** native v0.24, CRTC1/CRTC2, construct-first codec, selective execution and buyer tests were reported in research conversations and local packages. Unless indicated otherwise, they are **reported progress/plans, not independently reproducible evidence in this repository**.
- **Proposals:** v1.4.10 authenticated compiler-session optimization and further buyer-harness evaluation remain **unimplemented/unmeasured here**.

## 2. Transfer/cache engine lineage

### Native v0.22–v0.23 (checkpointed)

C++20/CMake implementation with native HTTP(S) full and ranged transfers, independent SHA-256, atomic content-addressed cache publication, resumable source/ETag-bound staging, locks, recovery and phase measurements. v0.23's Windows tests passed 3/3 CTest suites; curated Linux source rerun passed 3/3. In a balanced real-WAN Windows comparison (12 per method, 36 independently verified transfers), **curl + hash 1943.249 ms**, **native full GET 1988.228 ms**, **native four-worker ranges 1999.053 ms**. No network speedup was demonstrated. The v0.23 source is not present in this repository; v0.22 source was noted in a separate draft PR #4. See the linked checkpoint for detailed provenance.

### Native v0.24 causal-evaluator direction (planned)

An additive native causal evaluator, intended to preserve the transfer/cache path while handling original-property occurrence identity, simultaneous joining obligations, witness-grounded consequence propagation, provenance-preserving proof records, and explicit unknown/conflict outcomes. Related CRPP-16/17 and absence/nonconstruction work is **separate research**; do not describe it as shipping CRT v0.24 behavior without source and independent tests.

## 3. Compression / constructive-codec research

- **CRTC1 v0.1 reported illustrative cases:** types-only explicit 192,116 bytes -> constructive + zlib6 **129 bytes**; source histories explicit 1,505,323 bytes -> constructive + zlib6 **2,398 bytes**. These are highly structured cases, **not** a general-purpose compression ratio or verified independent buyer benchmark.
- **CRTC-G1:** reported exact source-ledger recovery through Python test workflow; needs preserved datasets, hash-verifiable round trips, resource budgets and independent decoder replay.
- **CRTC2 v0.3 proposed test matrix:** bandwidth 0.25 Mbps–1 Gbps, payloads from KB to hundreds of MB; structured, ordinary and incompressible inputs; warm/cold cache; paired repetitions with confidence intervals and selection regret; corruption, truncation, altered manifests, interrupted operations; final two-machine WAN validation.
- **Selector principle:** choose by verified end-to-end cost, not a fixed ideology favoring ConstructiveRT, gzip, or their composition. Reported illustrative choices include constructive at 0.75 Mbps and gzip at 100 Mbps; these are scenario-specific observations. Test ConstructiveRT -> gzip as its own candidate rather than assuming it must win.
- **Pricing discussed, not offered:** candidate one-time **$4.99** license with optional **$0.99/month** updates. No confirmed market demand, pricing test, sale, license grant, or revenue established.

## 4. Authenticated incremental compilation: CRT v1.4.6–v1.4.9

The local experiments distinguish initial fragment generation, authenticated changed-group reuse, cache validation, whole compilation, linking, source-proof patching, and compiler executable identity checking. The v1.4.9 controlled authoritative journal uses independent new-root anchors and sequential distinct rooted revisions; **not arbitrary C++ or arbitrary unauthenticated external edits**. Earlier v1.4.8 timing omitted a repeated compiler-executable hash from internally instrumented compile totals, motivating the full-wall-clock accounting in v1.4.9.

### CRT v1.4.9 Windows crossover (20 alternating pairs at each group count)

All timings in milliseconds. Medians include proof patch and the complete compiler identity check. Positive paired saving favors fragments. A paired-difference median is *not* equal in general to the subtraction of separately calculated build medians.

| Changed groups of 32 | Fragment median | Whole median | Median paired whole-minus-fragment | Fragment wins /20 | Paired median bootstrap 95% CI | Rebuilds needed to repay fragment setup |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 6 | 764.102 | 946.628 | +198.608 | 20 | [165.018, 207.344] | 10 |
| 8 | 865.816 | 959.627 | +75.492 | 19 | [58.917, 84.130] | 26 |
| 9 | 901.180 | 945.918 | +38.566 | 16 | [16.736, 58.855] | 51 |
| 10 | 961.762 | 951.691 | -21.846 | 6 | [-32.373, -0.921] | Not at reported median |
| 11 | 1010.812 | 947.479 | -56.326 | 2 | [-70.920, -31.218] | Not at reported median |
| 12 | 1056.748 | 948.266 | -119.977 | 1 | [-141.347, -103.715] | Not at reported median |

**Observed Windows decision boundary in this workload: fragment through 9 changed groups, whole from 10.** Group-level predictions matched all 6 cases; in 120 paired comparisons the selector's fixed six-count policy selected the empirically faster trial mode 106 times (88.3%). This is in-sample validation, **not** a portable or independently validated selection accuracy claim. Initial fragment build added **1930.8249 ms** relative to the root-pinned whole-only comparator. Initial fragment build **1930.8249 ms**, initial full cold startup combined **3210.827 ms**, and whole calibration **907.3898 ms** are different quantities and must not be conflated.

The supplied file reports **260 native execution checks** (240 compilation-mode builds + 20 default-linker-only trials); it reports no Windows `lld` link-only trials. Windows default linker median was **125.18 ms** in 20 trials. Linux, separately, showed default linker **68.0 ms** vs `lld` **32.1 ms** over 20 paired link trials; do **not** transfer that benefit to Windows without running `-TryLLD`.

Windows compiler-executable identity verification was approximately **0.33–0.38 seconds per build**, commonly around **0.35 s**, on *both* fragment and whole paths. This shared fixed overhead materially affects user-perceived latency but removing it symmetrically does not, by itself, prove a changed 9/10-group crossover.

### Limits on the evidence

The v1.4.9 file establishes benchmark-reported timings and successful native executable checks; it does **not** prove complete toolchain attestation, resistance to malicious local administrators, security against mutable DLLs, arbitrary compiler support, or deployment readiness. Source-history proof and object-cache proof must remain enforced independently of compiler identity optimization. The Linux and Windows sweeps are different environments; direct numerical comparison is descriptive, not a controlled cross-platform speedup claim.

## 5. Next priority: CRT v1.4.10 authenticated compiler session (not yet implemented)

**Goal:** avoid redundant full compiler-binary hashing during a controlled session *without weakening the guarantee that the actual executable bytes used are authenticated*.

Required experiment:
1. Baseline: full compiler-executable SHA-256 before **every** build; log identity hash time and total wall time.
2. Experimental session pin: authenticate the compiler image and its dependency/argument/environment closure; establish a platform-enforced link from authenticated bytes to what child processes execute. A cached digest or remembered filename/mtime **alone does not provide this**. Windows handle sharing semantics, image mapping, subprocess launch and DLL load behavior require explicit adversarial verification. If the guarantee cannot be established, treat the mode as **untrusted**.
3. Diagnostic unsafe hash-once mode allowed *only* as a negative control, never a trusted production path.
4. Alternate 20+ paired trials, repeat 100 authenticated builds per session, and record session startup, repeated enforcement, source proof checks, object integrity, compilation, linking, end-to-end time, and execution outcomes.
5. Negative controls: executable byte mutation, path replacement/rename, symlink/path substitution if supported, DLL/toolchain dependency mutation, argument/environment changes, source/object corruption, process/session interruption and restart, and race attempts at authentication-to-execution boundary. Fail closed where applicable.
6. Compare investment repayment using realistic distributions of changed groups, not a uniform fixed group count. Repeat the Windows linker comparison only where a compatible authenticated `lld` exists.

**Acceptance:** no unauthorized mutation silently accepted under the explicitly scoped threat model, original proof checks retained, full end-to-end overhead reproducibly reduced. No savings or security property claimed until measured.

## 6. Good Economy Agent integration / commercialization guardrails

The agent may **discover** ConstructiveRT as an owned asset and **draft** benchmark-backed value propositions or buyer tests. It must distinguish:
- native transfer/cache runtime vs CRTC codec vs authenticated incremental-build prototype;
- local benchmark results vs reproduced results vs proposals;
- byte savings vs elapsed time vs network throughput vs total operating costs;
- released source/license vs locally held prototypes;
- costs and net earned revenue vs speculative prices.

Recommended buyer evaluation: anonymous independent buyer harness, blind alternatives (ConstructiveRT / native full transfer / curl / gzip / composed pipeline as appropriate), pinned datasets, hash-verified outputs, paired timing with error bars, warm/cold cache, failure injection, and *no favoritism by construction*. Do not call a candidate commercially superior because it wins only on a synthetic structured case. Collect no payment or personally identifying buyer data without a separately authorized workflow. The Good Economy Agent remains dry-run/read-only in its applicable lanes; no product has been automatically published or sold by this documentation change.

## 7. Next evidence needed

- Commit the **redacted full v1.4.9 Windows JSON** (or a hash-pinned public copy) only after checking for local paths and sensitive metadata; preserve all 120 paired differences.
- Obtain actual Windows `lld` trials if available.
- Build/run v1.4.10 session-pinning *security and timing* experiments, then recalibrate the adaptive selector.
- Obtain independent two-machine transfer/codec buyer tests, exact source round trips and fault-injection evidence.
- Update Good Economy Agent asset runway only from verified source artifacts and explicit licensing/revenue evidence, not plans.

This document updates the research ledger only. It does not import ConstructiveRT source, modify agent execution logic, enable sales, or grant commercial licenses.
