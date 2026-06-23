# NEXT_STEPS

Updated: 2026-06-23

This file only lists unfinished work. Completed work belongs in `experiment_report.md`. If a claim changes, update `analysis/claim_evidence_map.md`.

---

## Current Gate

Current route:

```text
AAAI_2 is an oral-ambition safe RL deployment-evidence paper.
The first gate is the official AAAI-27 template plus literature novelty gate.
The second gate is a deployability-gap main phenomenon:
aggregate budget success can hide unsupported action-level safety claims.
```

Do not start broad benchmark work before Phase 0 and Phase 1 answer:

```text
Is the claim still novel after CAPS, AEGIS, BCRL, TREBI, and conformal shielding?
Can we show aggregate safety passing while action-level claim support fails?
Can ACCS improve certified utility and claim yield at matched claim miscoverage?
```

---

## P0. Literature and Template Gate

Status: in progress.

Tasks:

1. Keep the official AAAI-27 author kit in `aaai2027/`.
2. Maintain `papers/paper_index.csv`.
3. Read full PDFs for CAPS, AEGIS, BCRL, Robust Probabilistic Shielding, Conformal Safety Shielding, and DSRL/OSRL.
4. Decide the exact novelty boundary against CAPS:

```text
ACCS is a budget-uniform action certificate protocol,
not a generic constraint-adaptive policy-switching method.
```

Done condition:

```text
The introduction claim, baseline list, and threat map survive the direct competitors.
```

---

## P0b. Project Scaffolding

Status: in progress.

Tasks:

1. Keep `idea_blueprint.md` as the main paper route.
2. Maintain `EXPERIMENT_MANUAL.md`, `EXPERIMENT_FIX_PLAN.md`, `experiment_report.md`, `theory_proofs.md`.
3. Create code skeleton in `src/`.
4. Decide the exact toy environment schema and action group report format.

Done condition:

```text
All core workflow files exist and Phase 1 script interfaces are specified.
```

---

## P1. Deployability-Gap Toy Main Phenomenon

Goal:

```text
Build the upgraded Figure 1 / Table 1 prototype:
aggregate safety can pass while action-level claim support fails.
```

Implementation tasks:

1. Implement a simple gridworld/navigation toy in `src/toy_env.py`.
2. Generate offline trajectories under an aggressive behavior policy.
3. Train or fit a simple base policy and cost-return predictor.
4. Implement no-shield, a CAPS-like switching proxy if real CAPS is not integrated yet, global conformal, action-conditional ACCS.
5. Evaluate budgets `{3,5,8,10,15,25}`.
6. Report certified utility area, claim yield, claim miscoverage, unsupported safety success, abstention, and reward/cost.
7. Write outputs to `outputs/phase1_toy_moving_budget_server.json`.

Go criteria:

- at least one method passes aggregate cost while having low claim support;
- global conformal is safe but has low certified utility / claim yield;
- ACCS has better certified utility at matched claim miscoverage;
- CAPS-like switching proxy does not by itself provide provenance;
- group-wise coverage diagnostics are interpretable.

No-go handling:

- repair the toy distribution before scaling to Safety-Gymnasium.

---

## P2. ACCS Prototype

Tasks:

1. `src/conformal.py`: finite-sample quantile, group quantile, hierarchical fallback.
2. `src/action_groups.py`: action bucket and risk cluster APIs.
3. `src/shield.py`: execute / replace / abstain logic.
4. `src/eval_metrics.py`: U/C/A/H metrics.
5. JSON action-safety report schema.

Done condition:

```text
Phase 1 toy can output per-action safety reports and group-wise coverage tables.
```

---

## P3. Safety-Gymnasium Main

Start only after P1/P2 are clean.

Tasks:

1. Select 2-3 environments.
2. Freeze train/calibration/test splits.
3. Compare no-shield, global conformal, state-only, action-conditional, pessimism.
4. Run at least 5 seeds and multiple budgets.
5. Output `outputs/phase3_safety_gym_main_server.json`.

Go criteria:

- ACCS improves matched-risk reward or safe action set size.
- group coverage remains readable.
- abstention boundary is not overwhelming.

---

## P4. DSRL / Strong Baseline Expansion

Start only after Safety-Gym result is paper-positive.

Tasks:

1. DSRL dataset integration.
2. Offline safe RL baselines.
3. CAPS integration.
4. CAPS + ACCS and global conformal over CAPS.
5. retrain-per-budget optional upper bound.
6. DSRL-specific report schema.

---

## P5. Paper Writing

After Phase 1 positive:

1. Draft intro around fixed-budget safety failure.
2. Draft method around calibrate-or-abstain action-safety protocol.
3. Draft theorem section from `theory_proofs.md`.
4. Generate claim-evidence table.

---

## Maintenance Rules

After every completed action:

1. Move completed items from this file to `experiment_report.md`.
2. Update `analysis/reproduction_log.md` with commands and outputs.
3. Update `analysis/claim_evidence_map.md` if a paper-facing claim changes.
4. Preserve negative results and failed runs.
5. Do not add new broad experiments until the current gate is satisfied.
