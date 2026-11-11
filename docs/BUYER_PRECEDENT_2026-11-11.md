# Independent buyer-selection precedent v0.1 — 2026-11-11

## Purpose

Test whether an autonomous *buyer-side selection rule*, distinct from the owner's asset-income ranking, can select an owned engineering product based on verifiable customer utility **without being told to prefer it**. A valid precedent must include rejection cases and an auditable causal ledger. This is a **simulated procurement choice** and **not a sale or observed market demand**.

The seller-side Good Economy Agent's `asset-discovery` identifies candidate owned assets. The new `agent/buyer_precedent.py` is deliberately buyer-side: it receives candidate representations, observed transfer data, declared hypothetical prices, workload volume, and explicit constraints. It minimizes modeled monthly cost among methods meeting a latency SLA and a purchase-authorization ceiling. It can select `explicit`, `gzip`, `constructive`, or no eligible choice; no purchase interface exists.

## Source evidence used in the first local experiment

- Windows source-histories TSV: 95,408 bytes; SHA-256 `7a65ebcdc1d84d8a4acf41bd1e8a7f7979d425c97aad1f4e0faff259f45fd240`.
- gzip: 13,252 bytes; constructive CRTC2: 10,651 bytes. Compression is 86.11% vs 88.84% relative to the original source.
- Windows benchmark: 72 successful reported exact-source verifications across four controlled localhost application-layer network conditions, 6 repetitions per method per condition. No WAN claim.
- Buyer evaluator independently checks SHA-256 for all three supplied representation files and independently decompresses gzip to the exact source digest. It does **not** include a CRTC2 decoder and therefore audits, but does not independently reproduce, the CRTC2 decoding claim in the benchmark. The original test's verification records remain the source of that claim.
- Transfer times and reconstruction/verification wall-time medians are recomputed from the CSV and checked against the supplied benchmark summary. The source manifest is locally trusted, not authenticated as a remotely obtained production artifact.

## Commercial offer chosen for this experiment (not published)

- **$4.99 USD one-time, permanent license** to the purchased ConstructiveRT version. No recurring charge is required to continue using that version.
- **$0.99 USD/month optional update subscription**, enabled only by express opt-in; default is off. If cancelled, the buyer keeps using the paid-for version and any updates already acquired while eligible; future updates cease. Terms, distribution, support and refund policy need approval before sale.
- This is a *proposed* selling price, not a recorded sale or a published commercial listing. All buy-side mandates remain simulated.
- The update subscription cannot be silently bundled into the perpetual-license price or represented as mandatory.

## Buyer economics and synthetic mandates

The buyer evaluates a declared **12-month horizon** in the included examples. A $4.99 one-time purchase contributes $4.99/12 = approximately **$0.415833/month** to the comparison *only as an analysis convention*, not as a monthly charge. Optional updates contribute $0 unless the buyer explicitly opts in; opting in adds $0.99/month. Alternatives retain their own explicit prices.

Cost inputs remain synthetic: $0.09/decimal GB transferred, $0.03/core-hour multiplied by observed reconstruction-and-verification wall time as an approximate CPU proxy, and workload frequency declared by each buyer. Actual CPU utilization, full production costs and demand are unverified.

Four hypothetical mandates are included:
1. Small workload: reject the permanent license if its amortized value cannot beat free gzip.
2. Large workload: consider purchasing ConstructiveRT and independently opting in to updates where modeled benefit exceeds both fees.
3. Fast link with a strict 210ms median SLA: reject ConstructiveRT for latency regardless of price.
4. Large workload with $20/month assumed integration cost: reject when monthly spending permission is exceeded.

For eligible method `m`, source size `B_m`, monthly transfers `N`, egress rate `E`, reconstruction-and-verification wall-time proxy `R_m`, CPU rate `C`, one-time purchase `P_m`, evaluation horizon `H`, optional update charge `U_m`, and recurring integration assumption `I_m`:

`modeled_monthly_cost_m = B_m*N*E/1e9 + R_m*N*C/3_600_000 + P_m/H + U_m + I_m`

The buyer checks the *upfront purchase authority* against `P_m` separately from *monthly spending authority* against `U_m+I_m`, in addition to requiring the measured latency SLA. The buyer can select gzip, explicit, ConstructiveRT or no eligible method. The 12-month horizon is not an expiry of ownership and must not be confused with an update term.

**Evidence boundary:** The original 72 transfers were measured on one structured TSV under localhost network shaping, not a wide-area Hugging Face workload. The code checks source hashes but does not independently decode CRTC2. Xet's existing schemes remain unmeasured. No independent purchase, product delivery or revenue occurred.

## Reproduction

In the **private** repo, offline synthetic unit tests require only the standard library:

```powershell
py -m unittest discover -s tests -p test_buyer_precedent.py
```

To replay the original local experiment, obtain the owner's supplied Windows `summary.json`, `shaped_trials.csv`, `source.tsv`, `source.tsv.gz`, and `source.crtc` **without committing the source or local ledgers**:

```powershell
py -m agent.buyer_precedent `
    --summary ".\private-evidence\summary.json" `
    --trials ".\private-evidence\shaped_trials.csv" `
    --artifacts-dir ".\private-evidence" `
    --mandates ".\examples\buyer_mandates_simulated.json" `
    --out ".\outputs\buyer_precedent_report.json"
```

Read the emitted decision JSON. The script always reports `transaction_occurred: false` and `actual_revenue_usd: 0`. It has no spending, network, or public-write implementation.

## Hugging Face evaluation boundary

The authenticated Hugging Face account can discover Hub repositories, datasets, documentation, and Spaces, but this connection does **not** grant access to Hugging Face's internal purchasing agent or procurement authority. Hugging Face Xet currently documents `None`, `LZ4`, and byte-grouped `LZ4` chunk encodings. This first benchmark does **not** include Xet encodings, nor does the present source-histories codec demonstrate arbitrary `xorb`/model-file compatibility. These competitors are listed as **unmeasured**, not silently assumed inferior.

Next test: benchmark identical HF Xet reference data across actual feasible representations and independently verify complete source restoration, then repeat selection without changing the rules. Do not promote CRTC2 from a simulated choice to a real purchase until license, delivery, integration, independent third-party requirements, and actual buyer authority are established.

Relevant source: https://huggingface.co/docs/xet/xorb#picking-a-compression-scheme

## Ethics and settlement

This experiment remains compatible with `METHODOLOGY.md`: zero false buyer identities, no manufactured sales, no unauthorized expenditure, no economic wallet transfer, no false revenue, and separate positive benefit from negative ethics debt. Any future settled sale requires independent authorization, lawful opt-in value exchange, and recorded net costs.
## Local verification of revised $4.99 / $0.99 offer

Executed offline after the permanent-license price update (November 11, 2026):

- `python -m unittest discover -s tests -p test_buyer_precedent.py -v`: **8/8 passed** in the local isolated experiment. This is not GitHub Actions CI and is not the complete repository test suite.
- Replay against owner-provided **Windows** source-histories `summary(20261111-151328).json` + `shaped_trials(1).csv`, plus independently hash-checked representation artifacts: **72 recorded exact-source-verified trials**; independent gzip decoding verified; no independent CRTC2 decoder in the buyer script.
- Four decisions using the example mandates: small → gzip; large → constructive (with opt-in updates); fast strict SLA → gzip; large with $20/month modeled integration overhead against $10/month recurring authority → gzip (not authorized).
- Large scenario (100,000,000 hypothetical monthly downloads of the same 95,408-byte TSV): estimated monthly gzip cost $126.987167 versus constructive $108.884833, modeled savings **$18.102334/month** including $4.99/12 amortization and optional $0.99/month updates. No real-world purchase, customer demand, bandwidth bill or income established.
- Exact file content correspondence for the buyer script and tests was checked using Git blob hashes; local files include a trailing newline not present in those two GitHub source blobs, with byte-identical content otherwise.

**Selection precedent, not pricing validation:** Buyer rules were specified by the experimenter and replayed on a single structured workload. Do not interpret one synthetic positive decision as proof of conversion or product-market fit. Independent baseline comparison must include applicable Hugging Face Xet representations.
