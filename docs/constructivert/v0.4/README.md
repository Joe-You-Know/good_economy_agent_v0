# ConstructiveRT v0.4 mathematical notes (LaTeX)

Canonical source: [CRPP-1 and CRPP-2](CRPP_Residual_Propagation.tex).

**Status:** working conditional derivation; not a universal physical joining theorem or a performance claim.

The note establishes a scoped formulation for witnessed absence, residual preservation, arrangement-sensitive propagation, residual joining through a newly witnessed relationship, and causal-ledger invertibility. Revision 0.2 adds CRPP-3: scoped exclusivity/capacity, the distinction between admissible and witnessed joins, constrained propagation, preserved underdetermination, and conditional independence of noninterfering joins. A universal simultaneous-joining law, global completeness, and quantitative benefits remain open.

## Compilation

With a TeX distribution installed:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error .\CRPP_Residual_Propagation.tex
pdflatex -interaction=nonstopmode -halt-on-error .\CRPP_Residual_Propagation.tex
```

This research branch does not modify the Good Economy Agent runtime, any codec, or any buyer policy. New derivations should update the LaTeX source and its assumptions, proof status, counterexamples, and experimental contract together; they can then be reviewed by pull request.
