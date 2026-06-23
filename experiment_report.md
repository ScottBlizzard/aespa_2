# Experiment Report

> **Last updated**: 2026-06-23  
> **Project**: AAAI_2 / ACCS  
> **Rule**: paper-facing numbers must come from recorded server outputs under `outputs/*_server.json` or `outputs/*_server.md`, or from canonical assets under `analysis/paper_assets/`. Local runs are smoke tests only.

---

## Current Mainline

The current paper route is:

```text
Calibration After Action Selection: Safety Claims for Offline RL under Moving Budgets
```

Core thesis:

```text
Learned safe-RL cost or feasibility scores are not calibrated deployment certificates.
The main target is false certification among action claims issued after
deployment-time action selection and moving budget queries.
```

Evidence axes:

```text
U = utility retention
C = action-level calibration
A = retrain-free budget adaptivity
H = horizon-level risk audit
```

---

## Evidence Ledger

| Phase | Role | Key result | Status |
|---|---|---|---|
| Phase 0 | Protocol freeze | train/calibration/test split, action-safety report schema | pending |
| Phase 1 | Exact toy main phenomenon | marginal conformal failure after action selection | pending |
| Phase 2 | ACCS prototype | group-wise coverage and abstention reports | pending |
| Phase 3 | Safety-Gymnasium main | multi-budget, multi-seed benchmark | pending |
| Phase 4 | DSRL | stronger offline safe RL benchmark | pending |
| Phase 5 | Distribution shift | weighted/online recalibration boundary | pending |
| Phase 6 | Horizon audit | action-level vs episode-level risk | pending |

---

## Current Paper-Usable Claims

No experimental claims are paper-usable yet.

Conceptual claims currently supported by blueprint/theory only:

| Claim | Evidence status |
|---|---|
| Marginal conformal coverage does not imply selected-claim risk control. | conceptual / needs Phase 1 |
| Residual-cost certificates are continuation-policy-specific. | theory draft / needs implementation |
| Horizon-level safety is a separate boundary from action-level coverage. | theorem draft / needs audit |

---

## Claims That Must Stay Rejected Until Evidence Exists

| Rejected claim | Reason |
|---|---|
| ACCS guarantees safe RL trajectories. | Only action-level conformal guarantee is planned. |
| ACCS always controls episode-level violation. | Requires horizon audit and assumptions likely fail under shift. |
| ACCS beats all offline safe RL baselines. | No benchmark evidence yet. |
| Action grouping is universally best. | Must be shown by granularity and baseline sweeps. |
| Abstention is negligible. | Must report abstention rate and reasons. |
| Distribution shift is solved by weighted conformal. | Must be audited as mitigation only. |

---

## Canonical Outputs

No canonical server outputs yet.

Planned:

```text
outputs/phase0_protocol_freeze_server.json
outputs/phase1_toy_moving_budget_server.json
outputs/phase2_accs_prototype_server.json
outputs/phase3_safety_gym_main_server.json
outputs/phase4_dsrl_main_server.json
outputs/phase5_shift_audit_server.json
outputs/phase6_horizon_audit_server.json
analysis/paper_assets/*
```

---

## Run Log

| Date | Action | Output | Status |
|---|---|---|---|
| 2026-06-23 | Project workflow scaffold created locally. | workflow docs | completed |
| 2026-06-23 | Official AAAI-27 author kit downloaded and copied into `aaai2027/`. | `aaai2027.sty`, `aaai2027.bst`, examples, checklist | completed |
| 2026-06-23 | Phase 0 literature gate started. | `papers/paper_index.csv`, `papers/literature_review.md`, `analysis/literature_threat_map.md` | completed |
| 2026-06-23 | Phase 0 critical PDFs downloaded. | `papers/pdfs/`, `papers/pdf_manifest.csv` | completed |
| 2026-06-23 | Oral upgrade applied to project route. | `idea_blueprint.md`, `theory_proofs.md`, `analysis/claim_evidence_map.md`, `analysis/oral_upgrade_plan.md` | completed |
| 2026-06-23 | External review incorporated. | SafeFQL added; route changed to calibration after action selection; old Proposition 2 removed. | completed |
