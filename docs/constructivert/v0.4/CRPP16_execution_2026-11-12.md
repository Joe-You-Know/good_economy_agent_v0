# CRPP-16 execution cross-check — 2026-11-12

The existing bundled bounded benchmark was rerun in a Linux x64 environment using Node.js v22.16.0. A separate original CNF/DPLL symbolic solver was implemented and compared on the same 243 input ledgers; the existing Python CRTC-G1 codec from the user's earlier source archive was also executed for exact byte recovery.

## Logic

- 243 cases: 239 consistent, two explicit evidence conflicts, two inconsistent constraints.
- Original direct-vs-exhaustive rerun: zero unsound conclusions, zero missing entailments, zero JSON/DEFLATE roundtrip failures.
- New independent CNF/DPLL baseline: exact status/forced-conclusion agreement in **243/243** cases; 5,021 SAT calls, 24,270 branches, 29,291 recursive calls, 18,497 unit propagations.
- Direct: 3,907 candidate checks, 5,535 rule checks, 535 proof nodes, **zero hypothetical successful-join objects** and zero materialized model masks.
- Exhaustive reference: 246,784 candidate subsets, 1,233,920 hypothetical successful-join objects, 67,358 accepted models.
- The symbolic solver likewise avoids success-object materialization, but explores partial Boolean assignments. It is not an industrial optimized SAT solver.

## Five separate-process run medians

| Mode | Elapsed evaluation | Peak process RSS | Sampled heap increase |
|---|---:|---:|---:|
| Direct | 5.676 ms | 28,284 KiB | 1,091,592 B |
| Original exhaustive reference | 195.881 ms | 39,716 KiB | 2,844,992 B |
| New CNF/DPLL symbolic | 18.005 ms | 34,420 KiB | 1,089,600 B |

Results depend on this runtime, grammar, and algorithms. No all-allocation tracing or industrial-SAT comparison was performed.

## Actual Python CRTC-G1 codec roundtrip

The original Python implementation at `crcodec.general` was extracted from the user's prior `ConstructiveRT_CRTCG1_General_Data_2026-11-11.zip`, applied to two concatenated JSONL streams, and checked for byte-exact SHA-256 recovery.

| Payload | Raw bytes | CRTC-G1 bytes | Whole-stream gzip-6 bytes | CRTC-G1 encode/decode |
|---|---:|---:|---:|---:|
| 243 original ledgers | 53,124 | 16,901 | 3,559 | 5.928 / 2.959 ms |
| 243 ledgers + direct proof packets | 95,755 | 79,386 | 6,018 | 4.715 / 2.023 ms |

Both CRTC-G1 streams decoded **exactly**. Gzip compresses these streams more compactly. The stream-level gzip figures should not be conflated with prior per-case packet compression totals.

**Limitations:** This is *not* execution of the Windows native `crnative.exe` (absent in this container), nor a new CRPP-specific native codec. It demonstrates source-code codec roundtrip, not native binary integration or compression superiority.

The complete runnable scripts, console results, and Python codec output are in the separately delivered `CRPP16_execution_results_2026-11-12.zip` companion bundle. A GitHub Actions run on these new results was not performed.
