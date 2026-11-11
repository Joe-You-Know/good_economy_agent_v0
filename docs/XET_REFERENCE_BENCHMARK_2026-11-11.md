# Hugging Face Xet reference measurement — 2026-11-11

## Exact independent source validation

Using the public [Xet reference dataset](https://huggingface.co/datasets/xet-team/xet-spec-reference-files), a Hugging Face-hosted CPU-basic job downloaded the original Electric Vehicle Population CSV (63,527,244 bytes) and its official `.xorb` object (14,737,817 bytes). The Xorb yielded **796 chunks**, all marked LZ4. A four-byte `XETB` trailer was handled separately. Recombining decoded chunks reproduced the original file byte-for-byte; source SHA-256: `f41255b252f776125f2b657136654e4d4d5d2ccf8ef4db0ec186bd1981b69734`.

Remote execution: [Job record](https://huggingface.co/jobs/joe-you-know/6af48fe99737d9a9e0931296).

## Measured same-source alternatives

| Representation | Bytes | Median encode ms | Median decode ms | Exact source? |
| --- | ---: | ---: | ---: | --- |
| Official Xorb (as published) | 14,737,817 | — | — | Yes |
| Raw chunks plus 8-byte headers | 63,533,612 | 0.003 | 0.001 | Yes |
| Fresh per-chunk LZ4 | 14,679,039 | 81.679 | 44.619 | Yes |
| Fresh per-chunk byte-grouped LZ4 | 23,776,165 | 176.139 | 7,981.446 | Yes |
| Fresh per-chunk gzip-6 | 9,699,360 | 982.762 | 142.528 | Yes |
| **CRTC2 on this CSV** | **Unmeasured** | — | — | **Unmeasured** |

The recompressed alternatives use **the official Xet chunk boundaries**, with 8-byte per-chunk headers for a size-comparison convention. These are not generated official Xet containers, nor a network-transfer test. Python BG4 reverse-grouping is unusually expensive; do not extrapolate its timing to native Xet. The Xorb is an observed published artifact; its creation time is not benchmarked. All timings are from one CPU job with three local repetitions, and do not include transport latency, cold network cost, full application orchestration or integration cost.

## Unchanged autonomous buyer policy: **NO DECISION**

Do not substitute the older 95,408-byte structured-history CRTC2 benchmark for the 63,527,244-byte Xet CSV. The present evidence contains no verified compatible CRTC2 encoder/decoder output on this reference source and no comparable end-to-end verified-transfer medians across representations. Consequently, **ConstructiveRT was neither selected nor rejected as an economic competitor**.

The existing `agent/buyer_precedent.py` decision rule and the proposed **$4.99 perpetual license + opt-in $0.99/month updates** are unchanged. In local verification, `load_evidence` rejected a deliberately incomplete candidate manifest with `Methods differ from expected buyer alternatives`; it did not fill in the missing data. This is not a negative purchase decision.

### What an admissible comparison still requires

1. A CRTC2 encoder/decoder compatible with this arbitrary CSV or a fully specified general-purpose CRTC2 file form; produce and independently reconstruct the original SHA-256.
2. Common-host, common-source measurements of actual candidate representations, at equal network conditions, including separate verified-transfer wall times.
3. An **adapter** to map new Xet competitors into the buyer's inputs while preserving its decision criterion and authorization rules; do not relabel Xet as CRTC2 or silently drop alternatives.
4. Re-run the fixed price, update opt-in and buyer mandates without tuning thresholds after seeing the results.

This benchmark establishes a useful Xet baseline and a conservative refusal to claim unsupported ConstructiveRT selection. Real purchases and earned revenue remain $0.
