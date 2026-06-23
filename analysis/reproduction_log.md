# Reproduction Log

> **Last updated**: 2026-06-23  
> **Purpose**: Record commands, server runs, outputs, paper compiles, and artifact changes.

---

## Rules

1. Every server experiment command goes here.
2. Every downloaded output file goes here.
3. Every paper compile and generated figure/table goes here.
4. If a run is bad, record it rather than deleting it.
5. Paper-facing numbers must be traceable from this log to `experiment_report.md`.

---

## Environment Setup

No server environment setup recorded yet.

---

## Runs

| Date | Machine | Command / Script | Output | Status | Notes |
|---|---|---|---|---|---|
| 2026-06-23 | local | project scaffold created | workflow files | completed | No experiment run. |
| 2026-06-23 | local | `Invoke-WebRequest https://aaai.org/authorkit27/` and `Expand-Archive` | `aaai2027/official_author_kit/`, `aaai2027/aaai2027.sty`, `aaai2027/aaai2027.bst` | completed | Official AAAI-27 template downloaded from AAAI. |
| 2026-06-23 | local/web | literature search over OSRL moving-budget, shielding, conformal safety, and benchmark papers | `papers/*`, `analysis/literature_threat_map.md` | completed | CAPS identified as critical direct competitor. |
| 2026-06-23 | local/web | `Invoke-WebRequest` over critical paper PDF URLs | `papers/pdfs/*.pdf`, `papers/pdf_manifest.csv` | completed | 11 critical PDFs downloaded. |

---

## Paper / Asset Builds

| Date | Command | Output | Status |
|---|---|---|---|
| 2026-06-23 | `pdflatex -interaction=nonstopmode -halt-on-error paper.tex` in `aaai2027/` | `aaai2027/paper.pdf` | completed |
| 2026-06-23 | `pdflatex -interaction=nonstopmode -halt-on-error paper.tex` in `aaai2027/` after oral title/abstract upgrade | `aaai2027/paper.pdf` | completed |
