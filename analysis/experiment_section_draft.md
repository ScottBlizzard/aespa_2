# Experiment Section Draft

> Updated: 2026-06-24
> Source protocol: `analysis/main_table_protocol.md`

---

## Compact Outline

1. **Setup.** Define fixed query blocks, issued-claim risk, yield, and common
   audit/test splits.
2. **Baselines.** Compare unaudited top-reward selection, global candidate CP,
   reward-bin UCB, CRC-style thresholding, and ACCS-v0 support+safety.
3. **Direct trained proposers.** Evaluate CAPSIQL, CPQ, and COptiDICE on
   official DSRL `OfflineCarCircle-v0`.
4. **Risk-yield finding.** Show that global CP controls risk only by very low
   yield, while selective auditors preserve much higher yield.
5. **Stress and boundary.** Report residual-horizon stress and logged
   episode-block proxy evidence to separate action certificates from
   episode-level safety.

---

## Draft Text

**[setup]** We evaluate safety certification on fixed deployment query blocks
rather than on individual logged transitions. For each test state and residual
budget, a trained proposer generates a candidate action bank together with
reward, safety, and support scores. The deployment rule then selects or abstains
on one issued action claim. We report false certification among issued claims,
claim yield, and normalized reward, and we compare all auditors on the same
frozen query banks so that differences come from certification rules rather
than from changing the proposer distribution.

**[baselines]** The auditor suite separates proposal-level calibration from
post-selection certification. The unaudited row selects the top-reward action
from the candidate bank and reports its selected false-certification rate.
Global candidate CP calibrates a single threshold before selection. Reward-bin
UCB conditions on deployment reward score, and CRC-style thresholding selects a
safety threshold by expected-risk control. ACCS-v0 adds support-aware selection
over a prespecified finite rule family. We include reward-bin and CRC-style
auditors as strong baselines because the toy experiments show that simple
post-selection conditioning can already repair some selection-amplification
failures.

**[direct trained proposers]** Table X evaluates three trained offline safe-RL
proposers on official DSRL `OfflineCarCircle-v0`: CAPSIQL at 50k update steps,
CPQ at 10k update steps, and COptiDICE at 10k update steps. Each row averages
three seeds and uses the same query-bank/auditor contract. CAPSIQL q0.93 gives
the current trained CAPS-style mainline: candidate false certification is
4.42%, but top-reward selection raises the issued-claim false rate to 5.68%.
CPQ q0.92 and COptiDICE q0.92 are the high-signal direct OSRL rows, with
top-selected false-certification rates of 7.17% and 8.30%, respectively.

**[main finding]** Post-selection auditing reduces issued-claim risk while
preserving substantially more yield than global calibration. In the high-signal
CPQ row, ACCS-v0 reduces selected false certification from 7.17% to 2.25% while
keeping 80.18% yield. In the COptiDICE row, ACCS-v0 reduces selected false
certification from 8.30% to 2.17% with 78.33% yield. Global candidate CP has
lower risk, but it issues certificates on only 7.33% and 8.08% of these two
query blocks, respectively. The relevant comparison is therefore a risk-yield
tradeoff, not risk alone.

**[interpretation]** The table supports the paper's central claim that a learned
safety score is not itself a deployment certificate. The trained proposers are
reasonable offline safe-RL systems, and the candidate-level false rates are not
catastrophic. The failure appears after a deployment rule selects among
candidates and issues a claim. This is precisely the statistical object targeted
by selective safety certification.

**[horizon stress]** We stress the residual-label horizon on CPQ and COptiDICE
at q0.92. Changing the logged suffix label from H=40 to H=20 keeps the
selected-risk gap visible and gives high-yield audited rules: ACCS-v0 reaches
2.26% risk at 94.82% yield on CPQ and 2.13% risk at 93.00% yield on COptiDICE.
The harder H=80 setting is more revealing: ACCS-v0 remains below the 5% target
with 3.61%/80.13% on CPQ and 3.27%/84.93% on COptiDICE, while global or
reward-bin rules become much closer competitors. This supports the
moving-residual-budget motivation without turning action certificates into
closed-loop episode-safety claims.

**[episode proxy]** To make the boundary concrete, we group the same logged
test query blocks by their anchor episodes. This episode-block proxy is not a
simulator closed-loop guarantee, but it shows what is lost when action claims
are aggregated over many opportunities. On CPQ q0.92, ACCS-v0 has 2.25%
block-level selected false certification at 80.18% yield, yet 49.08% of issued
logged episodes contain at least one false issued claim. On COptiDICE q0.92,
the corresponding numbers are 2.17% block risk at 78.33% yield and 44.37%
episode-proxy false certification. This motivates explicit risk allocation or
a separate closed-loop audit for trajectory-level safety.

**[emission budget]** A sparse emission-budget sweep shows that risk allocation
is a live path rather than only a limitation. We reuse the same auditor masks
but cap certificate emission to 1/2/4/8 logged query blocks per episode.
ACCS-v0 with cap=1 reduces episode-proxy false certification to 0.46% on CPQ
and 0.69% on COptiDICE with 100% episode yield, while block yield drops to
2.42%. With cap=4, block yield rises to 9.67% and episode-proxy false remains
2.53%/2.64%; cap=8 begins to exceed the 5% target. This is not a closed-loop
guarantee, but it identifies the next design target: tune the number and timing
of certificates per episode under an explicit risk budget.

**[limitation]** These results certify action claims under the constructed
offline query law. They do not by themselves prove closed-loop episode-level
safety, robustness under arbitrary online adaptation, or safety for unsupported
actions. The separate policy-mismatch and no-overlap experiments motivate these
boundaries, and the next benchmark extension should test whether the same
risk-yield pattern survives broader DSRL environments or SafeFQL-style
proposers.

---

## Claim-Evidence Map

| Claim | Evidence | Status |
|---|---|---|
| Selection changes the relevant safety object from candidate risk to issued-claim risk. | `toy_selection_failure.csv`, `phase_strong_proposer_pilot_server.json`, `table_main_direct_osrl.md` | supported |
| Trained safe-RL proposers show nontrivial selected-claim risk under fixed query banks. | CAPSIQL/CPQ/COptiDICE rows in `table_main_direct_osrl.md` | supported on CarCircle |
| Global CP is low-yield rather than a practical solution in the trained rows. | Global yield 3.81%, 7.33%, and 8.08% in main rows | supported |
| ACCS-v0 provides useful risk-yield control in high-signal rows. | CPQ q0.92 and COptiDICE q0.92 ACCS risk/yield | supported |
| Residual-horizon changes preserve useful action-level risk-yield behavior. | `phase_dsrl_horizon_stress_summary.md` | supported on CarCircle |
| Action-level selected certification does not imply episode-level safety. | `phase_dsrl_episode_proxy_car_q92_summary.md` | supported as logged episode-block proxy; true closed-loop audit pending |
| Sparse emission budgeting can reduce episode-proxy false certification. | `phase_dsrl_episode_capsweep_proxy_car_q92_summary.md` | supported as logged cap sweep; tuneable/closed-loop budget pending |
| The current evidence proves closed-loop episode-level safety. | none | not supported; avoid |

---

## Self-Review Checklist

| Check | Status | Revision Need |
|---|---|---|
| One message per paragraph | pass | Each paragraph has setup, baseline, result, finding, interpretation, or limitation role. |
| Unsupported claims | pass | Episode-level and arbitrary-online claims are explicitly excluded. |
| Baseline fairness | pass | Same query-bank/auditor contract is stated. |
| Reviewer attack: CRC/reward-bin are strong | addressed | Draft explicitly keeps them as baselines and frames risk-yield rather than dominance. |
| Reviewer attack: only CarCircle | partly addressed | Ball/Drone robustness exists, but CarCircle remains the strongest headline stress. |
| Reviewer attack: action claims are not trajectories | addressed as boundary | Episode proxy documents the gap and motivates next risk-allocation/closed-loop work. |
| Reviewer attack: risk allocation is only speculative | partly addressed | Cap=1 proxy gives a positive sparse diagnostic, but closed-loop tuning remains future work. |
