# Main Table Protocol

> Updated: 2026-06-24
> Purpose: freeze the first paper-facing protocol for the direct OSRL/DSRL
> trained-proposer results.

---

## Reviewer-Facing Message

The main table should show that selection-aware safety certification is a
deployment-time evidence layer for trained offline safe-RL proposers. The table
must not claim that ACCS-v0 is the only possible selective-risk repair. The
stronger and more defensible claim is:

```text
Trained safe-RL proposers can have moderate candidate-level false rates but
higher false-certification rates after top-reward action selection. Post-
selection auditors reduce issued-claim risk to about 2.2-2.3% on the same
query blocks, while preserving roughly 78-81% yield in the high-signal rows.
```

The key reviewer distinction is risk-yield tradeoff. Global candidate CP often
has low selected risk only because it issues certificates on very few query
blocks. Reward-bin and CRC-style auditors are serious baselines and must remain
in the table.

---

## Frozen Evaluation Unit

Each row evaluates a fixed deployment query block:

```text
W = (s, B, {a_j}_{j=1}^K, reward_scores, safety_scores, support_scores)
```

The proposer distribution, candidate bank, residual labels, and train/audit/test
splits are frozen before comparing auditors. All auditors see the same query
bank and differ only in their certification rule.

Current common setting:

```text
environment: OfflineCarCircle-v0
dataset: official DSRL HDF5
K / proposal samples: 96
seeds: 20260624, 20260625, 20260626
residual-label source: logged-neighbor residual future cost under the fixed
                       checkpoint evaluator contract
auditors: unaudited top proposer, global candidate CP, reward-bin UCB,
          CRC-style safety threshold, ACCS-v0 support+safety
```

This protocol supports action-claim certification under the constructed query
law. It does not by itself prove horizon-level closed-loop safety. The logged
episode-block proxy in `outputs/phase_dsrl_episode_proxy_car_q92_summary.md`
is boundary evidence for this distinction, not a replacement for a true
closed-loop simulator audit. The cap=1 emission-budget proxy in
`outputs/phase_dsrl_episode_cap1_proxy_car_q92_summary.md` and the full cap
sweep in `outputs/phase_dsrl_episode_capsweep_proxy_car_q92_summary.md` are
sparse positive diagnostics for risk allocation, not replacements for the
high-yield action certificate table.

---

## Main Rows

Use these as the first main-table rows:

| Role | Proposer setting | Reason |
|---|---|---|
| Mainline trained CAPS-style row | CAPSIQL 50k, q0.93, reward-heavy scorer | closest current trained CAPS route; candidate false below 5%, selected false above 5% |
| Direct OSRL high-signal row | CPQ 10k, q0.92, model_best | direct named OSRL baseline with selected false above 7% |
| Direct OSRL stress row | COptiDICE 10k, q0.92, model_best | strongest direct OSRL selection stress so far, selected false above 8% |

Use these as stability/appendix rows:

| Role | Proposer setting | Reason |
|---|---|---|
| CPQ conservative stability | CPQ 10k, q0.93, model_best | lower raw risk, verifies non-vacuous ACCS behavior |
| COptiDICE conservative stability | COptiDICE 10k, q0.93, model_best | still nontrivial selected false, verifies robustness |
| Procedural bridge | CAPS-style CarCircle q0.92 risk0.25 support0.10 | high selected-risk bridge, not a trained checkpoint baseline |

Do not mix these roles in one table without explicit row labels.

---

## Current Main-Table Numbers

Canonical assets:

```text
analysis/paper_assets/table_main_direct_osrl.csv
analysis/paper_assets/table_main_direct_osrl.md
```

Summary:

| Setting | Candidate false | Top selected false | Global yield | Reward-bin risk/yield | CRC risk/yield | ACCS risk/yield |
|---|---:|---:|---:|---:|---:|---:|
| CAPSIQL 50k q0.93 | 4.42 +/- 0.43 | 5.68 +/- 0.25 | 3.81 | 3.59 / 71.71 | 2.67 / 83.52 | 2.28 / 80.60 |
| CPQ 10k q0.92 | 6.40 +/- 0.68 | 7.17 +/- 0.67 | 7.33 | 1.99 / 60.96 | 2.78 / 83.44 | 2.25 / 80.18 |
| COptiDICE 10k q0.92 | 6.36 +/- 0.57 | 8.30 +/- 0.76 | 8.08 | 3.12 / 57.94 | 2.28 / 79.15 | 2.17 / 78.33 |

Percentages are shown for readability. Source CSV values are in fractions.

---

## Claims Supported By This Table

Supported:

1. Selection-aware false certification is measurable on trained safe-RL
   proposers, not only on exact toys.
2. Direct CPQ and COptiDICE checkpoints create nontrivial selected-risk regimes
   under the same fixed query-bank/auditor contract.
3. Global candidate CP is not a practical main competitor in these rows because
   its low risk comes with very low yield.
4. ACCS-v0 support+safety preserves high yield while keeping selected false
   certification near 2.2-2.3% in the main high-signal rows.
5. CRC-style and reward-bin auditors remain serious baselines; the paper should
   emphasize the RL-specific protocol and support-aware certification target,
   not a blanket dominance claim.

Not yet supported:

1. True closed-loop episode-level safety improvement.
2. Robustness across BallCircle, DroneCircle, and harder environment families.
3. SafeFQL-specific superiority.
4. A theorem for arbitrary adaptive online deployment streams.

Boundary evidence:

1. The logged episode-block proxy shows that CPQ/COptiDICE q0.92 action-level
   ACCS risk near 2.2% can accumulate to 44-49% episode-proxy false
   certification when many claims are issued per logged episode.
2. The emission-budget sweep reduces ACCS episode-proxy false certification to
   0.46%/0.69% at cap1 and 2.53%/2.64% at cap4 for CPQ/COptiDICE, with cap8
   rising above the 5% target.

---

## Experiments Section Mini-Outline

1. **Setup.** Define fixed query blocks, residual labels, target risk/yield
   metrics, and the shared audit/test split.
2. **Phenomenon.** Show exact toy and synthetic OSRL-style query bank to explain
   why candidate-level calibration differs from selected-claim risk.
3. **Direct trained proposers.** Report CAPSIQL, CPQ, and COptiDICE on official
   DSRL CarCircle with the same auditors.
4. **Ablations and boundaries.** Report q0.92/q0.93, residual-horizon stress,
   logged episode-block proxy, procedural bridge, support/no-overlap, policy
   mismatch, and audit-size sensitivity.
5. **Limitations.** Separate action-claim certification from horizon-level
   closed-loop safety and from unsupported off-policy extrapolation.

---

## Self-Review

| Dimension | Status | Action |
|---|---|---|
| Contribution | pass | The table supports a deployment-time certification object, not another safe-RL optimizer. |
| Writing clarity | needs revision | Paper draft must define query law, residual label, and issued-claim risk before the table. |
| Experimental strength | pass for first main table | Three trained proposer families are replicated across three seeds. |
| Evaluation completeness | needs new experiment | SafeFQL and broader environments remain optional but reviewer-relevant. |
| Method design soundness | needs revision | State that this is finite-query-block certification, not full online safety. |
