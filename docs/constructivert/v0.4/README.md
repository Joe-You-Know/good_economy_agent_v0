# ConstructiveRT v0.4 mathematical notes (LaTeX)

Canonical source: [CRPP-1 and CRPP-2](CRPP_Residual_Propagation.tex).

**Status:** working conditional derivation; not a universal physical joining theorem or a performance claim.

The note establishes a scoped formulation for witnessed absence, residual preservation, arrangement-sensitive propagation, residual joining through a newly witnessed relationship, and causal-ledger invertibility. Revision 0.2 added CRPP-3: scoped exclusivity/capacity, the distinction between admissible and witnessed joins, constrained propagation, preserved underdetermination, and conditional independence of noninterfering joins. A universal simultaneous-joining law, global completeness, and quantitative benefits remain open.

## Compilation

With a TeX distribution installed:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error .\CRPP_Residual_Propagation.tex
pdflatex -interaction=nonstopmode -halt-on-error .\CRPP_Residual_Propagation.tex
```

This research branch does not modify the Good Economy Agent runtime, any codec, or any buyer policy. New derivations should update the LaTeX source and its assumptions, proof status, counterexamples, and experimental contract together; they can then be reviewed by pull request.

## Revision 0.3: simultaneous joint determination (CRPP-4)

Distinguishes a witnessed **joint encounter boundary** from individually admissible competing candidates. A complete, sound joint response law with an existing unique causally distinguishable outcome is sufficient for conditional determination without imposing a pairwise order. Exclusivity alone cannot select a winner. The actual primitive joint response law, unconditional uniqueness, global completeness, and performance benefits remain open. Revision 0.3 also repairs accidental duplicated text in the prior LaTeX document.

## Revision 0.4: witnessed contact and shared constraint (CRPP-5)

Formalizes a witnessed multilateral contact as a distinct incidence from individual pairwise admissibilities. Derives that contact and necessary shared constraints alone do **not** select closure, while a complete, sound jointly sufficient response law with existence and uniqueness does conditionally determine closure and typed residuals. Includes the cases of incompatible exclusive-port reuse, partially fulfilled joint interfaces, and underdetermined outcomes. The missing universal primitive response law and direct nonenumerative execution remain open.

## Revision 0.5: grounded unavoidable outcome (CRPP-6)

Separates mutually consistent requirements, complete shared-contact laws, and actual outcome realization. Defines a finite grounded forcing certificate from original witnesses and scoped laws, with source-preserving coverage of causally distinct rivals; proves a **conditional** uniquely determined joint closure when a result is required/realized and sufficient closure conditions hold. Includes anchored and unanchored three-participant examples, and a no-positive-closure residual case. Universal physical sufficiency, symmetry breaking, and global proof-search bounds remain open.

## Revision 0.6: original-contact incidence sufficiency (CRPP-7)

A witnessed common encounter with complete, compatible source-specific coverage of an independently specified incidence relation suffices for its **relational closure** without hypothetical intermediate joins. Pairwise contacts alone do not prove a common encounter; completed contact does not determine subsequent physical dynamics. Keeps later obligations typed as pending, defeated, or conflicting, and preserves exact causal provenance. Next: derive whether independently witnessed changes in original participation relationships entail specific physical consequences without assuming a response law.

## Revision 0.7: propagation of witnessed relational change (CRPP-8)

Distinguishes persistent original relationships, verified absent-to-present changes, and unknown-to-present observations that do not prove creation. Adds source-scoped transition witnesses, sound propagation obligations, grounded partial-consequence certificates and a conditional criterion for uniquely determined subsequent constructions. Before/after correlation does not independently establish a causal mechanism. The complete primitive transition law and runtime efficiency remain open.

## Revision 0.8: cross-relation propagation within one encounter (CRPP-9)

Derives sound forcing from witnessed relational change plus a genuinely shared original obligation. Includes a formal compatible-transition semantics, a local proof certificate, an exclusive-interface example, derived consistency of a scoped value relationship without claiming physical contact, and a nonforcing shared-occurrence counterexample. Excluding a candidate arrangement does not witness absence of its original property. Global completeness, an unconditional primitive joint-response law, and runtime benefits remain unproved.

## Revision 0.9: shared constraints from incompatible original co-requirements (CRPP-10)

Shows how a local exclusion can be **derived without a primitive numeric capacity counter** when two proposed joins require independently established incompatible conditions on the same original property respect, source and encounter scope. Includes an explicit non-inference result: one observed failure of simultaneous joining cannot prove a general coexistence law. Source-preserving exclusion certificates, a minimal incompatibility explanation and counterexamples for independent interfaces and unknown observations are included. Deriving incompatibility itself from physical primitive construction and global runtime benefits remains open.

## Revision 0.10: witnessed resistance and scoped causal constraint (CRPP-11)

Distinguishes a pending/unfulfilled join from an actually witnessed joining attempt with conclusively observed nonfulfillment. Such evidence yields a **scoped obstruction and typed residual**, not an automatic force law or universal incompatibility. A transferable cross-join exclusion requires a separate, independently justified original-property dependency. Includes attempted-participation witnesses, resistance certificates, causal-attribution limits, controlled-contrast and noncontact counterexamples. Next: derive warranted property-specific coexistence limits from contact-response contrasts.

## Revision 0.11: transferable property-specific constraints (CRPP-12)

Separates repeated observed contact-response patterns, causal identification by controlled original-property contrasts, and **scoped transport** of the established response condition to new original occurrences. Proves a conditional transfer theorem only where an independently justified sound invariance law and a non-outcome-defined encounter-domain correspondence hold. Distinguishes observed recurrence, defeasible empirically supported prediction, and deductively certified transfer; documents hidden-condition and scope-changing counterexamples. Exact source and witness histories remain distinct. Next: derive/test constructive invariance directly from original face-to-face joining obligations.

## Revision 0.12: minimal source-preserving transfer support (CRPP-13)

Defines consequence-relative sufficient supports and **subset-minimal** distinction sets under a fixed source-scoped joining law; distinguishes sound proof from true minimality (counterexample or complete entailment check required), shows that multiple minimal supports can exist, and defines structure-preserving correspondence of relevant original properties, shared-occurrence identity within each encounter, orientations, and scoped law applications. Proves conditional transfer of a grounded consequence to a new witnessed source without enumerating hypothetical successful join histories. Next: extract original-property dependencies directly from contact-response witnesses and audit necessity against independently constructed counterexamples.

## Revision 0.13: direct original-dependency extraction and exact inversion (CRPP-14)

Separates the **complete exact original causal ledger**, **target-specific sufficient original witness support**, and **grounded dependency trace**. Defines source-scoped multi-premise rule instances extracted by following actual witness-supported implications, not enumerating hypothetical successful joins. Establishes soundness of a traced support; distinguishes relevance to one proof from subset-minimality and global essentiality, which require complete entailment or compatible counterexamples. Specifies two-layer ledger/certificate recovery, alternative proofs, genuinely joint antecedents, and a demonstrated failure of lossless reconstruction if irrelevant historical distinctions are discarded. Global minimization, cyclic completeness, and performance savings remain open.

## Revision 0.14: reproducible bounded verification (CRPP-15)

Added [`bounded_dependency_verifier.js`](./bounded_dependency_verifier.js). Run with `node docs/constructivert/v0.4/bounded_dependency_verifier.js` from the repository root. It compares **two different evaluators** over one explicitly declared four-join grammar: (1) a reference exhaustive enumerator that constructs hypothetical successful join objects for 16 subsets, and (2) direct witness-grounded constraint propagation without those objects. Six initial cases were executed in the JavaScript tool runtime (separate Node/GitHub CI execution not yet verified), including multi-premise simultaneous obligation, two independent exclusion proofs, two distinct irrelevant-history ledgers, unknown evidence, and contradictory reports. All six checks passed. Across five nonconflicting cases reference allocated **160 hypothetical join objects** over **80 candidate subsets**, while the direct procedure allocated **zero such objects**. This measures only this object class, **not total allocations, memory, time, global completeness or ConstructiveRT speedups**. Exact JSON-case roundtrip was checked; a real codec/decoder inversion test remains outstanding.

## Revision 0.15: broader verification with serialization and resources (CRPP-16)

Reproducible test files:
- [CRPP16_broader_verifier.js](./CRPP16_broader_verifier.js): `node docs/constructivert/v0.4/CRPP16_broader_verifier.js`
- [CRPP16_isolated_bench.js](./CRPP16_isolated_bench.js): run in separate processes with `node --expose-gc docs/constructivert/v0.4/CRPP16_isolated_bench.js direct` and repeat with `oracle`, each five times.

Evaluated locally using Node 22.16.0 on Linux x64: 10 joins, four conjunctive obligations, 243 deterministic ledgers (240 generated, three focused). Three initially missing negative entailments were addressed by grounded joint-obligation contrapositive propagation. In the final local run there were zero unsound, zero missing and zero JSON/DEFLATE roundtrip failures.

Direct: zero hypothetical successful join objects, zero hypothetical model masks; 3,907 candidate specifications examined, 5,535 rule checks and 535 proof nodes. Exhaustive: 246,784 subsets, 1,233,920 hypothetical join objects, 246,784 subset masks, and 67,358 accepted models.

Compressed bytes over 243 separately compressed cases: original ledgers only 37,663; original ledgers plus direct proof certificates 81,639; original ledgers plus exhaustive accepted model masks 207,370. These wire packets use JSON/Base64/DEFLATE, NOT the native ConstructiveRT codec; the exhaustive baseline also stores more information.

Five isolated process runs median: direct 5.10 ms, exhaustive 195.22 ms; peak process RSS approximately 27.7 MiB versus 39.5 MiB; approximate sampled heap increases 1.04 MiB versus 2.71 MiB. Memory measurements are coarse and the exhaustive reference is intentionally expensive. No superiority over a competent symbolic/SAT baseline, native ConstructiveRT codec, or general physical joint laws is established.

The JavaScript benchmark was executed locally before commit; no separate GitHub Actions or downloaded-commit execution is claimed.


## Revision 0.16: CRPP-17 causal-complexity falsification and repair

An independently implemented Python CNF/DPLL verifier tested **240 new native C++ cases** across 8/16/32/64 joins and five source-scoped causal families: overlapping exclusive ports, alternative joint obligations, chains, cyclic implications, and incompatible forks of mandatory consequences.

**Unpatched v0.24 was not complete** for the new family: it missed 16 necessary negative conclusions out of 240 cases, all in the fork-conflict tests. This prompted a source-grounded law: if jointly required antecedents would force two mutually incompatible original joining consequences, the conjunction of those antecedents is unavailable. A particular unestablished antecedent can be excluded when all the others are witnessed; no hypothetical successful joins need be materialized.

A small additive C++ experimental patch implements this local conflict rule. After the patch: 240/240 native results match the independent SAT oracle, with zero byte-recovery failures. The prior 243 native-vs-JS-vs-symbolic-vs-exhaustive cases still pass, with no proof discrepancies, as do all five Linux native test suites.

**Scope:** This is a bounded theorem and experimental correction, not a complete general-purpose inference engine or established speed advantage over optimized SAT. Native elapsed timings include process startup; Python SAT timings do not. The executable source package and `Run_CRPP17_Windows.cmd` were delivered as a separate Windows-ready ZIP in the conversation; **this patch has not yet been independently compiled on Windows**.

See the `CRPP-17` section of [CRPP_Residual_Propagation.tex](./CRPP_Residual_Propagation.tex) for the theorem, proof, counterexample, and limitations.
