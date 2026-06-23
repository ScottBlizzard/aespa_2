# Claim-Evidence Map

> **Last updated**: 2026-06-23  
> **Scope**: AAAI_2 abstract/introduction claim audit.  
> **Rule**: every major claim must point to a theorem, table, figure, canonical server output, or be weakened.

---

## Abstract / Introduction Claims

| Claim | Required evidence | Status |
|---|---|---|
| Aggregate fixed-budget safety is not deployment safety evidence. | Deployability-gap toy: aggregate cost passes while claim yield/provenance fails. | pending |
| Safety should be issued as action-level claims with calibration provenance. | Formal claim tuple + JSON action-safety report schema + theorem. | pending |
| ACCS builds a budget-uniform certificate surface. | Proposition on post-hoc budget thresholding + unseen-budget sweep. | pending |
| Strong constraint-adaptive policies still need an evidence layer. | CAPS vs CAPS+ACCS: claim yield, miscoverage, certified utility. | pending |
| ACCS adapts to unseen budgets without retraining. | Same calibrated certificate surface evaluated on unseen budgets; adaptation latency reported. | pending |
| Action-conditioned conformal certificates are less conservative than global certificates. | Matched claim-miscoverage frontier and certified utility area. | pending |
| ACCS controls accepted action-level violation risk. | Proposition 1/2 + group-wise empirical coverage. | pending |
| Abstention is necessary under sparse/OOD action evidence. | Sparse group stress test + abstention reason breakdown. | pending |
| Horizon-level safety is a separate boundary. | risk allocation theorem + episode violation audit. | pending |
| Distribution shift can degrade coverage but is diagnosable. | shift experiments with coverage degradation by group/time. | pending |

---

## Reviewer Questions

| Question | Planned answer | Status |
|---|---|---|
| Is this just conformal prediction plus safe RL? | Moving constraints + action-safety claim protocol + abstention + group diagnostics. | conceptual |
| Did CAPS already solve this? | CAPS adapts policies; ACCS issues calibrated action claims and can wrap CAPS. | pending |
| Why action-conditioned instead of global conformal? | Global over-conservatism at matched claim miscoverage; action group residual heterogeneity and provenance. | pending |
| Does action-level coverage imply safe trajectories? | No; we explicitly separate `C` and `H`. | theory draft |
| Are groups tuned on test data? | Protocol freeze: groups fixed before test. | pending |
| Is abstention hiding failure? | Report abstention rate/reasons and utility cost. | pending |
| Are baselines strong enough? | Include no shield, global/state conformal, pessimism, OSRL baselines, CAPS, CAPS+ACCS, optional retrain upper bound. | pending |

---

## Claims To Avoid

| Avoided claim | Reason |
|---|---|
| ACCS guarantees safe RL. | Only action-level guarantee under exchangeability. |
| ACCS solves sequential distribution shift. | Sequential shift is a boundary and empirical audit target. |
| Conformal shielding is distribution-free in deployment. | Policy-induced shift can break assumptions. |
| Action conditioning is always better. | It trades conservatism for sample support; must show granularity sweep. |
| Abstention is negligible. | Must be measured; may be a real cost. |
| ACCS beats retrained policies. | Retrain-per-budget is an expensive upper bound; not necessary for core claim. |
| ACCS is the first method for changing constraints. | CAPS/TREBI/BCRL/AEGIS occupy that space; ACCS is an evidence layer. |

---

## Canonical Evidence Assets

Planned:

| Asset | Role |
|---|---|
| `outputs/phase1_toy_moving_budget_server.json` | Deployability-gap toy table and certified utility metrics. |
| `outputs/phase2_accs_prototype_server.json` | Group-wise coverage and ACCS diagnostics. |
| `outputs/phase3_safety_gym_main_server.json` | Main benchmark table. |
| `outputs/phase4_caps_accs_server.json` | CAPS vs CAPS+ACCS evidence-layer comparison. |
| `outputs/phase5_shift_audit_server.json` | Distribution shift boundary. |
| `outputs/phase6_horizon_audit_server.json` | Horizon-level risk audit. |
| `analysis/paper_assets/table_main.csv` | Paper table generated from canonical outputs. |

---

## Current Verdict

No experimental claim is supported yet. The paper has a stronger oral-ambition thesis after the upgrade: deployment safety should be treated as issued action claims with provenance. The next decisive step is Phase 1 deployability-gap toy phenomenon.
