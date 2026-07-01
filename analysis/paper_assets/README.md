# Paper Assets

Updated: 2026-07-01

This directory contains compact paper-facing assets generated from local toys,
trained DSRL/OSRL audits, closed-loop diagnostics, and paper figure scripts.

## Figures

| File | Source | Role |
|---|---|---|
| `figure1_selection_amplification_hardened.pdf` | `src/toy_selection_failure_hardened.py` | main local phenomenon and hardened baselines |
| `figure1_sensitivity_hardened.pdf` | `src/toy_selection_failure_hardened.py` | audit-size/gamma/delta sensitivity |
| `figure2_policy_mismatch.pdf` | `src/toy_policy_mismatch.py` | continuation-policy residual mismatch |
| `figure3_no_overlap.pdf` | `src/toy_no_overlap.py` | no-overlap/support impossibility toy |
| `../../figures/figure4_offpolicy_shift.pdf` | `src/toy_offpolicy_shift.py` | off-policy query-shift diagnostic; main-text boundary sentence plus appendix/theory support |
| `../../aaai2027/tikz_figures.tex` | manual TikZ/PGFPlots rewrite from paper-facing assets | current main-paper Figure 1 and Figure 2 source; uses LaTeX body fonts |
| `../../figures/figure2_audit_layers.pdf` | `scripts/make_audit_layers_figure.py` | retained generated reference for the three-layer audit figure: action-level risk-yield, episode-proxy accumulation, closed-loop fixed-cap audit |

The current `aaai2027/paper.tex` uses the TikZ/PGFPlots figure source rather
than the generated PDF figures for its two main figures. The generated PDFs are
retained as reproducible assets and visual references.

The off-policy shift toy writes its table to
`../../outputs/toy_offpolicy_shift.csv` and a readable summary to
`../../outputs/toy_offpolicy_shift_summary.md`. It supports a concise
main-text diagnostic paragraph and the appendix table; it is not a replacement
for the trained DSRL benchmark evidence.

## Tables

| File | Role |
|---|---|
| `table_toy_k16.csv` | compact K=16 selection-amplification table |
| `table_policy_mismatch_k16.csv` | compact K=16 policy-mismatch table |
| `table_no_overlap_k16.csv` | compact K=16 no-overlap table |
| `table_strong_proposer_pilot_server.csv` | compact A40 synthetic strong-proposer pilot table |
| `table_dsrl_car_official_k64_q93_seeds.csv` | official DSRL CarCircle K64/q93 three-seed bridge |
| `table_dsrl_car_capsstyle_k64_q93_seeds.csv` | official DSRL CarCircle CAPS-style K64/q93 three-seed bridge |
| `table_dsrl_car_capsstyle_grid.csv` | official DSRL CarCircle CAPS-style focused q/risk/support one-seed grid |
| `table_dsrl_car_capsstyle_q92_risk025_support010_seeds.csv` | official DSRL CarCircle CAPS-style q0.92 high-signal five-seed bridge |
| `table_dsrl_bc_heads_diagnostics.csv` | trained weighted-BC multi-head proposer diagnostic |
| `table_dsrl_capsiql_checkpoint_grid_q92.csv` | 5k CAPSIQL checkpoint q0.92 scorer-weight diagnostic grid |
| `table_dsrl_capsiql_checkpoint_pilots.csv` | CAPSIQL checkpoint pilot summary generated from JSON outputs |
| `table_dsrl_capsiql_checkpoint_50k_q93_seeds.csv` | canonical trained CAPSIQL 50k q0.93 three-seed table |
| `table_dsrl_cpq_checkpoint_pilots.csv` | CPQ checkpoint pilot summary generated from JSON outputs |
| `table_dsrl_cpq_checkpoint_10k_all.csv` | all CPQ 10k checkpoint evaluator outputs |
| `table_dsrl_cpq_checkpoint_10k_q92_modelbest_seeds.csv` | trained CPQ 10k q0.92 model_best three-seed direct-baseline table |
| `table_dsrl_cpq_checkpoint_10k_q93_modelbest_seeds.csv` | trained CPQ 10k q0.93 model_best three-seed stability table |
| `table_dsrl_coptidice_checkpoint_pilots.csv` | COptiDICE checkpoint pilot summary generated from JSON outputs |
| `table_dsrl_coptidice_checkpoint_10k_all.csv` | all COptiDICE 10k q0.92/q0.93 model_best evaluator outputs |
| `table_dsrl_coptidice_checkpoint_10k_q92_modelbest_seeds.csv` | trained COptiDICE 10k q0.92 model_best three-seed direct-baseline table |
| `table_dsrl_coptidice_checkpoint_10k_q93_modelbest_seeds.csv` | trained COptiDICE 10k q0.93 model_best three-seed stability table |
| `table_main_direct_osrl.csv` | consolidated CAPSIQL/CPQ/COptiDICE direct-OSRL main-table asset |
| `table_main_direct_osrl.md` | human-readable direct-OSRL main table with percentage metrics |
| `table_main_direct_osrl.tex` | `booktabs` LaTeX draft of the direct-OSRL main table |
| `table_dsrl_horizon_stress.csv` | CPQ/COptiDICE q0.92 residual-horizon stress table for H=20 and H=80 |
| `table_dsrl_cpq_horizon_stress.csv` | CPQ-only residual-horizon stress diagnostic |
| `table_dsrl_ball_drone_10k_q92_feasibility.csv` | one-seed CPQ/COptiDICE BallCircle/DroneCircle broader-environment feasibility table |
| `table_dsrl_ball_drone_10k_q92_feasibility.md` | readable broader-environment feasibility summary |
| `table_dsrl_coptidice_checkpoint_ball_10k_q92_modelbest_seeds.csv` | three-seed COptiDICE BallCircle q0.92 model_best robustness table |
| `table_dsrl_episode_proxy_car_q92.csv` | CPQ/COptiDICE q0.92 logged episode-block proxy table; scope-boundary evidence, not closed-loop guarantee |
| `table_dsrl_episode_cap1_proxy_car_q92.csv` | CPQ/COptiDICE q0.92 episode emission-budget proxy table with one issued certificate per logged episode |
| `table_dsrl_episode_capsweep_proxy_car_q92.csv` | CPQ/COptiDICE q0.92 episode emission-budget sweep over caps 1/2/4/8 |
| `table_dsrl_episode_capsweep_proxy_car_q92.tex` | compact `booktabs` LaTeX table for the paper's episode emission-budget proxy |
| `table_dsrl_closed_loop_audit_car_30x30_diagnostic.csv` | three-seed online closed-loop 30/30 diagnostic summary; not a paper main table yet |
| `table_dsrl_closed_loop_audit_cpq_car_100x100_diagnostic.csv` | three-seed CPQ online closed-loop 100/100 fixed-rule audit summary |
| `table_dsrl_closed_loop_audit_coptidice_car_100x100_diagnostic.csv` | three-seed COptiDICE online closed-loop 100/100 stress summary |
| `table_dsrl_closed_loop_fixed_cap_car_100x100_diagnostic.csv` | pre-registered first-cap three-seed online closed-loop 100/100 CPQ/COptiDICE summary |
| `table_dsrl_closed_loop_fixed_cap_car_100x100.tex` | paper-ready compact LaTeX table for the pre-registered first-cap closed-loop audit |
| `table_dsrl_closed_loop_fixed_cap_ball_matched_100x100_diagnostic.csv` | matched BallCircle pre-registered first-cap three-seed online closed-loop 100/100 CPQ/COptiDICE summary |
| `table_dsrl_closed_loop_fixed_cap_ball_matched_100x100.tex` | compact LaTeX table for the BallCircle first-cap closed-loop audit |
| `table_dsrl_closed_loop_fixed_cap_drone_matched_100x100_diagnostic.csv` | matched DroneCircle pre-registered first-cap three-seed online closed-loop 100/100 CPQ/COptiDICE boundary diagnostic |
| `table_dsrl_closed_loop_fixed_cap_drone_matched_100x100.tex` | compact LaTeX table for the DroneCircle first-cap closed-loop boundary diagnostic |
| `table_dsrl_closed_loop_fixed_cap_frontier_200x200_20260630_4090.csv` | 4090 Car/Ball fixed-cap closed-loop frontier over caps 1/2/4/8, 3 seeds x 200 audit / 200 test |
| `table_dsrl_closed_loop_fixed_cap_frontier_drone_200x200_20260630_4090.csv` | 4090 Drone fixed-cap boundary frontier over caps 1/2/4/8, 3 seeds x 200 audit / 200 test |
| `table_dsrl_closed_loop_fixed_cap_frontier_all_200x200_20260630_4090.csv` | earlier combined Car/Ball/Drone fixed-cap closed-loop frontier over caps 1/2/4/8; superseded for paper-facing claims |
| `table_dsrl_closed_loop_fixed_cap_frontier_caps64_200x200_20260630_4090.csv` | intermediate Car/Ball/Drone fixed-cap closed-loop frontier over caps 1/2/4/8/16/32/64 |
| `table_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090.csv` | current paper-facing Car/Ball/Drone fixed-cap saturation frontier over caps 64/128/256/512 |
| `table_dsrl_closed_loop_tuned_rule_tuned_rule_100x200x200_20260630_4090.csv` | first 4090 tune/audit/test closed-loop diagnostic; appendix candidate, not a main-table replacement |
| `table_dsrl_closed_loop_tuned_rule_tuned_rule_drone_conservative_200x300x300_20260630_4090.csv` | conservative Drone-only tune/audit/test follow-up; too sparse for promotion |
| `table_dsrl_closed_loop_tuned_rule_tuned_rule_drone_medium_200x300x300_20260630_4090.csv` | medium Drone-only tune/audit/test follow-up; remains above the 5% target |

The strong-proposer table is a synthetic OSRL-style pilot, not a real benchmark
claim. It is suitable for internal paper planning and method debugging. The
first real benchmark-shaped table is now the consolidated CAPSIQL/CPQ/COptiDICE
direct-OSRL table; SafeFQL and broader DSRL/Safety-Gymnasium environments remain
stress-test or comparator expansion targets.

The DSRL/CAPS diagnostic outputs are mostly not paper assets. The exception is
the official DSRL CarCircle K64/q93 bridge table, which is useful for internal
paper planning but should still be labeled as logged-neighbor real-data evidence,
not CAPS/OSRL evidence.

The q0.92 CAPS-style bridge table is currently the strongest official DSRL
bridge asset. The q0.93 bridge remains useful as a more conservative stability
check. Neither table is a trained CAPS/OSRL checkpoint result.

The BC-heads diagnostic table is not a main result. It records that the first
trained-head scaffold runs, but its current nearest-logged-action matching
protocol does not create a strong selection-amplification gap.

The CAPSIQL checkpoint pilot table is the new trained-proposer route. The first
paper-shaped three-seed result is:

```text
outputs/phase_dsrl_capsiql_checkpoint_50k_q93_summary.md
analysis/paper_assets/table_dsrl_capsiql_checkpoint_50k_q93_seeds.csv
candidate false 0.044240 +/- 0.004336,
top selected false 0.056833 +/- 0.002501,
ACCS-v0 risk 0.022756, yield 0.806000
```

Treat q0.92 scorer grids and smoke runs as diagnostics. The q0.93 / 50k /
reward-heavy protocol is the current canonical trained-checkpoint setting until
multi-seed results say otherwise.

The CPQ checkpoint tables are the first replicated direct OSRL baseline assets.
They should be read as baseline expansion rather than replacement for the
CAPSIQL mainline: q0.93 model_best is conservative, while q0.92 model_best
exposes a stronger selected-risk regime with mean ACCS-v0 risk 0.022509 at
yield 0.801778.

The COptiDICE checkpoint tables are the second replicated direct OSRL baseline
asset. q0.92 model_best has mean top selected false 0.082972 and ACCS-v0 risk
0.021666 at yield 0.783250; q0.93 still has mean top selected false 0.058556
and ACCS-v0 risk 0.021973 at yield 0.831194. This is now a strong candidate
for the direct-baseline stress-test row in the main table.

The first consolidated direct-OSRL main table is now frozen in
`table_main_direct_osrl.csv`, `table_main_direct_osrl.md`, and
`table_main_direct_osrl.tex`. Its intended paper message is risk-yield tradeoff
rather than blanket dominance: global CP has low risk but only about 3.8-8.1%
yield, reward-bin and CRC-style auditors are serious baselines, and ACCS-v0
keeps selected-claim risk near 2.2-2.3% with about 78-81% yield in the
high-signal CPQ/COptiDICE rows.

The first residual-horizon stress table is now in
`table_dsrl_horizon_stress.csv` with the readable summary
`outputs/phase_dsrl_horizon_stress_summary.md`. CPQ and COptiDICE were rerun at
q0.92 for H=20 and H=80 over three seeds each. H=20 gives high-yield ACCS-v0
control: CPQ 2.26% / 94.82% and COptiDICE 2.13% / 93.00%. H=80 is a harder
moving-budget stress: ACCS-v0 remains below 5% at 3.61% / 80.13% for CPQ and
3.27% / 84.93% for COptiDICE, while global/reward-bin/CRC baselines become
closer competitors. This is residual-label stress evidence, not closed-loop
episode-safety evidence.

The first broader-environment trained-checkpoint feasibility pass is in
`table_dsrl_ball_drone_10k_q92_feasibility.csv` and
`table_dsrl_ball_drone_10k_q92_feasibility.md`. CPQ and COptiDICE were trained
for 10k update steps on BallCircle and DroneCircle for seed 20260624, then
audited at q0.92 under the same fixed query-bank contract. The one-seed
COptiDICE BallCircle row looked promising, but the three-seed follow-up changes
the interpretation: mean top false is 4.85%, mean selection gap is -0.29%, CRC
is 2.82% / 91.73%, and ACCS-v0 is 2.48% / 88.61%. BallCircle is therefore a
robustness/stability result rather than a stronger headline stress row than
CarCircle. DroneCircle is also a low-risk robustness supplement: CPQ DroneCircle
top false is 3.04% and COptiDICE DroneCircle top false is 3.19%. The later
matched BallCircle first-cap closed-loop audit is stronger than this direct
action-level robustness row: CPQ gives 0/300 test false issued episodes with
exact CP95 0.99%, while COptiDICE gives 256/300 test false issued episodes
with exact CP95 88.59%.

The first logged episode-block proxy is in `table_dsrl_episode_proxy_car_q92.csv`
with the readable summary `outputs/phase_dsrl_episode_proxy_car_q92_summary.md`.
It groups the same CPQ/COptiDICE q0.92 test query blocks by their anchor logged
episode. This is not a simulator closed-loop guarantee. Its value is to make the
scope boundary concrete: CPQ ACCS-v0 keeps block risk at 2.25% with 80.18%
yield, but 49.08% of issued logged episodes contain at least one false issued
claim; COptiDICE ACCS-v0 keeps block risk at 2.17% with 78.33% yield, while the
episode-proxy false rate is 44.37%. Use this as motivation for future
risk-allocation or closed-loop episode auditing, not as a replacement for the
action-certificate main table.

The emission-budget follow-up is in `table_dsrl_episode_capsweep_proxy_car_q92.csv`
and the paper-ready LaTeX table is in
`table_dsrl_episode_capsweep_proxy_car_q92.tex`
with summary `outputs/phase_dsrl_episode_capsweep_proxy_car_q92_summary.md`.
It uses the same logged episode-block proxy but caps certificate emission to
1/2/4/8 query blocks per episode. ACCS-v0+cap1 has 2.42% block yield and
reduces episode-proxy false certification to 0.46% on CPQ and 0.69% on
COptiDICE. ACCS-v0+cap4 raises block yield to 9.67% while keeping
episode-proxy false certification at 2.53% on CPQ and 2.64% on COptiDICE.
Treat this as an upper-bound risk-allocation diagnostic, not a replacement for
the high-yield action-level main table.

The current strongest true online closed-loop result is the 4090 fixed-cap
frontier in
`table_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090.csv` with
readable summary
`outputs/phase_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090_summary.md`.
It evaluates pre-registered fixed-cap rules with caps 64/128/256/512 over
three seeds and 200 audit / 200 test episodes per seed. CPQ cap512 has 12/600
test false issued episodes on CarCircle with exact CP95 3.22%, and 0/600 on
BallCircle with exact CP95 0.50%, while saturating the full CarCircle/BallCircle
episodes. COptiDICE remains a matched unsafe stress contrast: 365/600 test
false issued episodes on CarCircle and 533/600 on BallCircle. DroneCircle is a
boundary diagnostic: CPQ has 90/600 test false issued episodes with exact CP95
17.61%, while COptiDICE has 576/600 with exact CP95 97.23%.
The main paper now pairs this table with an exact fixed-emission
Clopper-Pearson audit corollary, so the closed-loop claim is stated as a
fixed-rule episode audit rather than an adaptive threshold-family guarantee.

The first tune/audit/test closed-loop diagnostic is in
`table_dsrl_closed_loop_tuned_rule_tuned_rule_100x200x200_20260630_4090.csv`
with readable summary
`outputs/phase_dsrl_closed_loop_tuned_rule_tuned_rule_100x200x200_20260630_4090_summary.md`.
It uses 100 tune / 200 audit / 200 test online episodes per checkpoint seed:
tune selects a small frozen rule family, then audit/test evaluate that frozen
rule. CPQ CarCircle and BallCircle stay positive, COptiDICE stays unsafe, and
CPQ DroneCircle improves from the fixed-cap full result 90/600 with CP95
17.61% to 32/395 with CP95 10.73%. This is a useful focused-search diagnostic
but not a promoted result because DroneCircle remains above the 5% target and
the selected rules vary across seeds.
Two focused Drone-only follow-ups confirm that more threshold/cap sweeps are not
worth running without a new method idea: the conservative 200/300/300 search is
too sparse for inference (CPQ 1/4 test false, CP95 75.14%), and the medium
200/300/300 search remains above target (CPQ 54/581, CP95 11.52%).

The first true online closed-loop diagnostic summary is in
`table_dsrl_closed_loop_audit_car_30x30_diagnostic.csv` with readable summary
`outputs/phase_dsrl_closed_loop_audit_car_30x30_summary.md`. It uses three
CPQ and three COptiDICE CarCircle checkpoints with 30 audit and 30 test
episodes per seed. The first historical paper-facing fixed-rule audit was the
pre-registered first-cap diagnostic in
`table_dsrl_closed_loop_fixed_cap_car_100x100_diagnostic.csv` with readable
summary `outputs/phase_dsrl_closed_loop_fixed_cap_car_100x100_summary.md`.
It issues certificates for the first cap policy steps in every online episode
and fits no score threshold on audit labels. CPQ has 1/300 false issued audit
episodes, giving a 1.57% exact 95% upper bound; the independent test splits
have 5/300 false issued episodes, giving a 3.47% exact 95% upper bound.
COptiDICE has 169/300 false issued audit episodes and 188/300 false issued
test episodes, giving exact 95% upper bounds of 61.15% and 67.32%.

The matched BallCircle version is in
`table_dsrl_closed_loop_fixed_cap_ball_matched_100x100_diagnostic.csv` with
readable summary
`outputs/phase_dsrl_closed_loop_fixed_cap_ball_matched_100x100_summary.md`.
It uses the same fixed first-cap accounting over three CPQ and three COptiDICE
BallCircle checkpoints. CPQ has 0/300 false issued audit episodes and 0/300
false issued test episodes, giving exact 95% upper bounds of 0.99% on both
splits. COptiDICE has 253/300 false issued audit episodes and 256/300 false
issued test episodes, giving exact 95% upper bounds of 87.69% and 88.59%.

The matched DroneCircle version is in
`table_dsrl_closed_loop_fixed_cap_drone_matched_100x100_diagnostic.csv` with
readable summary
`outputs/phase_dsrl_closed_loop_fixed_cap_drone_matched_100x100_summary.md`.
It uses the same fixed first-cap accounting over three CPQ and three COptiDICE
DroneCircle checkpoints. This is a boundary diagnostic rather than a third
positive environment: CPQ has 45/300 false issued audit episodes and 46/300
false issued test episodes, giving exact 95% upper bounds of 18.82% and
19.18%. COptiDICE has 289/300 false issued audit episodes and 294/300 false
issued test episodes, giving exact 95% upper bounds of 97.93% and 99.13%.

The earlier score-threshold matched fixed-rule audits are in
`table_dsrl_closed_loop_audit_cpq_car_100x100_diagnostic.csv` and
`table_dsrl_closed_loop_audit_coptidice_car_100x100_diagnostic.csv`, with
readable summaries `outputs/phase_dsrl_closed_loop_audit_cpq_car_100x100_summary.md`
and `outputs/phase_dsrl_closed_loop_audit_coptidice_car_100x100_summary.md`.
Across three CPQ checkpoints with 100 audit and 100 test episodes per seed, the
fixed emitted-cap rule has 4/300 false issued audit episodes, giving a
one-sided exact binomial 95% upper bound of 3.03%; the independent test splits
have 7/300 false issued episodes, giving a 4.34% exact 95% upper bound.
COptiDICE has mean test violation 61.67% in the matched 100/100 stress
diagnostic and 131/231 false issued test episodes, giving a 62.20% exact 95%
upper bound. Treat the CPQ fixed-rule result as the promising closed-loop
positive case and COptiDICE as the matched stress contrast. The 4090 fixed-cap
frontier should now be cited first; the older first-cap route remains useful
historically because it has no adaptive threshold-selection penalty. Do not
treat the adaptive threshold-family UCB as solved.
