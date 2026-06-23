# AAAI_2: When Constraints Move

This repository is the working directory for the AAAI_2 project:

```text
When Constraints Move: Action-Conditional Conformal Shields for Offline Safe RL
```

The intended paper is not a generic "conformal + safe RL" method paper. The current thesis is:

```text
Fixed-budget safe RL performance is not deployment safety evidence.
Deployment safety should be reported as calibrated, budget-conditioned,
action-level claims with explicit abstention when evidence is insufficient.
```

## File Map

| Path | Purpose |
|---|---|
| `idea_blueprint.md` | Full paper blueprint and oral-level positioning. |
| `EXPERIMENT_MANUAL.md` | Local/server workflow, commands, dependencies, run rules. |
| `EXPERIMENT_FIX_PLAN.md` | Known risks, failed-experiment triage, redesign plans. |
| `NEXT_STEPS.md` | Only unfinished work. Completed work moves to `experiment_report.md`. |
| `experiment_report.md` | Canonical evidence ledger. Paper numbers must come from here or listed assets. |
| `theory_proofs.md` | Definitions, theorem sketches, empirical predictions, evidence status. |
| `src/` | Code under development. |
| `outputs/` | Downloaded server outputs and local smoke outputs. |
| `analysis/` | Claim-evidence maps, adversarial review, paper assets, reproduction logs. |
| `papers/` | Literature notes and boundary analysis. |
| `aaai2027/` | Paper draft directory. |

## Working Rule

Local Windows work is for code, analysis, writing, and smoke tests. Official experiment numbers must come from 4090/A40 server outputs named `*_server.json` or `*_server.md`, then be recorded in `experiment_report.md`.

