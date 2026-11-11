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

## Explicitly synthetic buying mandates

All mandates in `examples/buyer_mandates_simulated.json` are illustrative; no prices, budgets, or projected copy counts are represented as observed customer behavior. Cost proxy: network egress at $0.09/GB, reconstruction-and-verification wall time multiplied by $0.03/core-hour, as a **rough** CPU-cost proxy (not CPU utilization evidence). The constructive license is a hypothetical $9/month, not a published quote for CRTC2. Integration costs are set by each mandate, and all alternative license fees are explicitly declared.

| Synthetic mandate | Selected | Estimated monthly gzip | Estimated monthly selected | Interpretation |
| --- | --- | ---: | ---: | --- |
| Small: 1M downloads, bandwidth limited | gzip | $1.269872 | $1.269872 | $9 hypothetical license not justified |
| Large: 100M downloads, bandwidth limited | constructive | $126.987167 | $116.479000 | $10.508167 modeled net saving after license; not actual demand |
| Fast-clean, strict 210ms median SLA | gzip | $127.373833 | $127.373833 | Constructive misses median SLA (211.762ms) |
| Large, extra $20/month setup with $20 spend limit | gzip | $126.987167 | $126.987167 | $29 license/setup exceeds synthetic authorization |

The 100M-download scenario repeats the *same 95KB example* at an assumed scale; it does not prove a real distribution exhibits that volume or codec benefit. No simulated buyer has funded authority, and no payment took place. Real income = $0.

## Decision rule and audit boundaries

For eligible method `m` (sample size `B_m`, number of monthly transfers `N`, network cost per decimal GB `E`, reconstruction/verification wall time `R_m` in milliseconds, imputed CPU cost per hour `C`):

`estimated_monthly_cost_m = B_m*N*E/1e9 + R_m*N*C/3_600_000 + license_fee_m + amortized_integration_cost_m`

Eligibility requires the measured scenario median transfer wall time `<= max_verified_transfer_ms` and the stated fee + integration `<= monthly_spend_authority_usd`. The method with the smallest modeled cost wins, tie-breaking by faster median wall time then method name.

The model deliberately **omits** unmeasured production availability, native integration effort, encoding amortization, cache distribution, data-specific modeling losses, request overhead, HTTP/TLS retransmits, CPU utilization, vendor support, legal/license verification, and operational/security requirements. Those must be added for production procurement. Neither this rule nor source SHA verification constitutes a functioning payment authority.

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