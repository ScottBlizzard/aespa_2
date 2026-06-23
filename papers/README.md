# Literature Notes

This directory collects literature notes and the Phase 0 critical PDFs.

PDF policy:

```text
papers/pdfs/          only critical Phase 0 papers and direct baselines
paper_index.csv       triage index for searched papers
pdf_manifest.csv      local PDF filenames and source URLs
literature_review.md  novelty verdict and positioning
code_reuse.md         reusable code/baseline plan
references.bib        literature-gate bibliography
```

## Required Literature Buckets

| Bucket | Purpose |
|---|---|
| Offline safe RL | CQL-Lagrangian, BCQ-Lagrangian, CPQ, COptiDICE, DSRL baselines. |
| Conformal prediction | split conformal, weighted conformal, online conformal, risk control. |
| Safe shielding | action shields, safety filters, control barrier functions where relevant. |
| Deployment shift | constraint shift, policy shift, offline-to-online mismatch. |
| Selective prediction / abstention | calibrate-or-abstain framing. |

## Note Format

For each paper:

```text
Title:
Venue/year:
Core contribution:
What it already solves:
What it does not solve for AAAI_2:
Baseline relevance:
Citation key:
```
