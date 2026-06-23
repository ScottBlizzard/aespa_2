# NEXT_STEPS

Updated: 2026-06-23

This file only lists unfinished work. Completed work belongs in `experiment_report.md`. If a claim changes, update `analysis/claim_evidence_map.md`.

---

## Current Gate

Current route:

```text
AAAI_2 is an oral-ambition safe RL deployment-evidence paper.
The first gate is the official AAAI-27 template plus literature novelty gate.
The second gate is an exact selection-failure phenomenon:
marginal calibration can fail after deployment-time action selection.
```

Do not start broad benchmark work before Phase 0 and Phase 1 answer:

```text
Is the claim still novel after CAPS, SafeFQL, AEGIS, BCRL, TREBI, RPS, and conformal safety shielding?
Can we show ordinary global/group conformal is nominal over proposals but fails among selected issued claims?
Can selection-aware ACCS control false certification while retaining useful claim yield and utility?
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
ACCS is a selection-aware finite-data auditor for learned action-feasibility scores,
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

## P1. Exact Selection-Failure Toy

Goal:

```text
Build the upgraded Figure 1 / Table 1 prototype:
ordinary conformal calibration can fail after action selection.
```

Implementation tasks:

1. Implement an exact finite MDP or one-state K-action construction in `src/toy_selection_failure.py`.
2. Define exact residual-cost distributions under a declared continuation policy.
3. Generate calibration/proposal streams with nominal marginal conformal coverage.
4. Select the highest-reward certified action among `K in {2,4,8,16}` candidates.
5. Compare uncalibrated score, global CP, group CP, conformal risk control, selective/FCR baseline, and selection-aware ACCS.
6. Report false certification among issued claims, claim yield, risk-coverage, reward, fallback/abstention, and support diagnostics.
7. Write outputs to `outputs/phase1_toy_moving_budget_server.json`.

Go criteria:

- global/group conformal achieves nominal marginal coverage over proposals;
- selected-action false certification substantially exceeds alpha;
- the failure worsens with candidate-set size K;
- selection-aware ACCS or a selective/FCR baseline restores target false certification;
- ACCS retains nontrivial claim yield and utility in supported regions;
- unsupported regions trigger abstention/fallback.

No-go handling:

- do not scale to Safety-Gymnasium / DSRL until the exact selection-failure phenomenon is clean.

---

## P2. ACCS Prototype

Tasks:

1. `src/conformal.py`: global and group split-conformal primitives.
2. `src/risk_control.py`: conformal risk control and selective/FCR baseline hooks.
3. `src/proposal_stream.py`: fixed proposal/query-bank interface.
4. `src/selection.py`: highest-reward certified action and alternative selection rules.
5. `src/support.py`: support diagnostics and no-overlap abstention.
6. `src/eval_metrics.py`: false certification, claim yield, risk-coverage, utility, fallback cost.
7. JSON issued-claim report schema with proposal distribution and continuation policy fields.

Done condition:

```text
Phase 1 toy can output selected-claim false certification, claim yield,
risk-coverage, fallback metrics, and support diagnostics.
```

---

## P3. Safety-Gymnasium Main

Start only after P1/P2 are clean and exact toy shows a substantial selection-induced calibration gap.

Tasks:

1. Select 2-3 environments only after exact toy success.
2. Freeze proposal streams, train/calibration/test splits, budgets, groups, alpha, and fallback.
3. Compare global CP, group CP, CRC/selective baseline, selection-aware ACCS, CAPS if feasible, SafeFQL if feasible.
4. Run at least 5 seeds and multiple budgets.
5. Output `outputs/phase3_safety_gym_main_server.json`.

Go criteria:

- selection-aware ACCS controls issued-claim false certification better than global/group CP.
- claim yield and utility remain nontrivial in supported regions.
- fallback/abstention boundary is measured and not hidden.

---

## P4. DSRL / Strong Baseline Expansion

Start only after exact toy and policy-specific calibration validation are paper-positive.

Tasks:

1. DSRL dataset integration.
2. Offline safe RL baselines.
3. SafeFQL comparison.
4. CAPS integration.
5. CAPS + global CP, CAPS + group CP, CAPS + selection-aware ACCS.
6. AEGIS/BCRL comparison if reproducible.
7. retrain-per-budget optional upper bound.
8. DSRL-specific report schema.

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
