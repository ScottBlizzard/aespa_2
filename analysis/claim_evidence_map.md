# Claim-Evidence Map

> **Last updated**: 2026-06-23  
> **Scope**: AAAI_2 abstract/introduction claim audit.  
> **Rule**: every major claim must point to a theorem, table, figure, canonical server output, or be weakened.

---

## Abstract / Introduction Claims

| Claim | Required evidence | Status |
|---|---|---|
| Learned cost/feasibility estimates are not calibrated deployment certificates. | Exact toy showing marginal calibration before selection but high false certification after selection. | pending |
| Ordinary marginal conformal does not control issued-claim risk after action selection. | Global/group CP vs selected-action false certification counterexample. | pending |
| ACCS targets false certification among issued claims. | Selection-aware theorem or conformal-risk-control style guarantee + toy evidence. | pending |
| Residual-cost certificates are policy-specific. | Formal `Z_H^{pi_cont}` target + simulator branching / exact toy validation. | pending |
| No support implies abstention is necessary. | No-overlap impossibility theorem + sparse/OOD support stress test. | pending |
| Strong constraint-adaptive policies still need finite-data auditing. | CAPS vs CAPS+global CP vs CAPS+group CP vs CAPS+selection-aware ACCS. | pending |
| SafeFQL is prior work, but does not close selection-aware moving-budget auditing. | Full SafeFQL reading + direct comparison or precise limitation. | pending |
| Horizon-level safety is a separate boundary. | risk allocation theorem + episode violation audit. | pending |
| Distribution shift can degrade coverage but is diagnosable. | shift experiments with coverage degradation by group/time. | pending |

---

## Reviewer Questions

| Question | Planned answer | Status |
|---|---|---|
| Is this just conformal prediction plus safe RL? | Reframe as calibration after action selection; ordinary conformal is a baseline expected to fail. | conceptual |
| Did CAPS already solve this? | CAPS filters actions; ACCS audits false certification after CAPS-style action selection. | pending |
| Did SafeFQL already solve this? | SafeFQL calibrates a learned safety boundary; ACCS must target selected-claim risk under candidate/budget queries. | pending |
| Why action-conditioned instead of global conformal? | The main issue is selection-aware false certification, not just group conditioning. | pending |
| Does action-level coverage imply safe trajectories? | No; we explicitly separate `C` and `H`. | theory draft |
| Are groups tuned on test data? | Protocol freeze: groups fixed before test. | pending |
| Is abstention hiding failure? | Report abstention rate/reasons and utility cost. | pending |
| Are baselines strong enough? | Include global CP, group CP, CRC, selective/FCR baseline, CAPS chain, SafeFQL, AEGIS/BCRL where feasible. | pending |

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
| ACCS is the first conformal offline safe RL method. | SafeFQL and conformal safety methods exist. |
| Accepted actions are safe because marginal conformal coverage holds. | False; selection can concentrate coverage failures. |

---

## Canonical Evidence Assets

Planned:

| Asset | Role |
|---|---|
| `outputs/phase1_toy_moving_budget_server.json` | Exact selection-failure toy table and false-certification metrics. |
| `outputs/phase2_accs_prototype_server.json` | Group-wise coverage and ACCS diagnostics. |
| `outputs/phase3_safety_gym_main_server.json` | Main benchmark table. |
| `outputs/phase4_caps_accs_server.json` | CAPS vs CAPS+ACCS evidence-layer comparison. |
| `outputs/phase5_shift_audit_server.json` | Distribution shift boundary. |
| `outputs/phase6_horizon_audit_server.json` | Horizon-level risk audit. |
| `analysis/paper_assets/table_main.csv` | Paper table generated from canonical outputs. |

---

## Current Verdict

No experimental claim is supported yet. The paper's viable oral-ambition thesis is now selection-aware calibration after action selection. The next decisive step is an exact toy counterexample showing that marginal conformal calibration fails among selected/issued action claims.
