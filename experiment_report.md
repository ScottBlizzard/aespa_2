# Experiment Report

> Last updated: 2026-07-01
> Scope: completed results that are useful for paper claims, experimental decisions, or reproducibility.
> Rule: this file records what we have already learned. Unfinished work belongs in `NEXT_STEPS.md`.

---

## Current Paper State

Current title:

```text
A Safety Score Is Not a Certificate:
Calibration After Action Selection in Offline RL
```

Current thesis:

```text
Marginal safety estimates can be valid before action selection but fail as
deployment-time certificates after a policy or planner selects actions. The
paper targets false certification among issued action or episode claims.
```

Current AAAI draft:

```text
aaai2027/paper.tex
aaai2027/paper.pdf
```

The draft currently contains the abstract, introduction, related work, problem
setup, theory spine, method, main DSRL table, residual-horizon stress paragraph,
logged-episode boundary evidence, the 4090 pre-registered fixed-cap
closed-loop table, tuned-rule and off-policy diagnostic sentences,
TikZ/PGFPlots figures, diagnostic/scope sections, and conclusion. The latest
local build satisfies the AAAI 7-page main-text budget: `paper.pdf` is 8 pages
and page 8 starts with `References`. The log scan found no undefined citations,
rerun warnings, overfull boxes, or TeX errors.

Current figure and supplement sources:

```text
aaai2027/tikz_figures.tex
aaai2027/appendix.tex
aaai2027/appendix.pdf
outputs/render_checks/paper_4090_page-1.png ... outputs/render_checks/paper_4090_page-8.png
outputs/render_checks/appendix_4090_page-1.png ... outputs/render_checks/appendix_4090_page-6.png
outputs/render_checks/paper_claim_audit_page-1.png ... outputs/render_checks/paper_claim_audit_page-8.png
outputs/render_checks/appendix_claim_audit_page-1.png ... outputs/render_checks/appendix_claim_audit_page-6.png
```

The previous generated PDF figures remain useful assets, but the main draft now
uses TikZ/PGFPlots for Figures 1 and 2 so their fonts are controlled by LaTeX
and visually consistent with the AAAI body text.

Latest integrated 4090 fixed-cap evidence:

```text
outputs/phase_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090_summary.md
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090.csv
```

### 2026-06-30 Paper Packaging Update

Useful changes:

| Issue | Current resolution |
|---|---|
| Related Work placement | Moved immediately after the introduction, before problem setup and method. |
| Figure font and editability | Replaced the two main included PDF figures with TikZ/PGFPlots figures defined in `aaai2027/tikz_figures.tex`. |
| Closed-loop evidence coverage | Main text now includes the 4090 full-cap Car/Ball/Drone fixed-cap closed-loop table; appendix keeps the saturation sweep over caps 64/128/256/512. |
| Fixed episode-audit theory | Added an exact-binomial fixed emission-rule corollary tied to the 4090 fixed-cap closed-loop audit. |
| Extra experiment evidence | `aaai2027/appendix.tex` collects residual-horizon stress, logged episode caps, closed-loop audit details, broader-environment feasibility, and negative diagnostics. |

### 2026-07-01 Claim-Audit Rewrite

Useful changes:

| Issue | Current resolution |
|---|---|
| Main line | Retitled the draft to `A Safety Score Is Not a Certificate: Calibration After Action Selection in Offline RL` and made the abstract/intro center on the certificate target. |
| Claim coverage | Added `analysis/reviewer_claim_audit_20260701.md`, mapping each manuscript claim to reviewer objections and evidence. |
| Useful diagnostics | Promoted the tuned-rule Drone result and the off-policy query-shift toy as concise main-text boundary evidence, while keeping full tables in the appendix. |
| Layout | Compressed reproducibility/conclusion text so the final build remains 8 pages with page 8 starting at `References`; appendix remains 6 pages. |

---

## Paper-Facing Evidence

### 1. Exact Local Phenomena

Useful assets:

```text
outputs/toy_selection_failure.csv
outputs/toy_selection_failure_hardened.csv
outputs/toy_policy_mismatch.csv
outputs/toy_no_overlap.csv
figures/figure1_selection_amplification_hardened.pdf
figures/figure1_sensitivity_hardened.pdf
analysis/local_results_summary.md
```

Key results:

| Diagnostic | Main useful result |
|---|---|
| Selection amplification | At K=16, a 4% per-action false rate becomes about 48% selected false certification under top-reward selection. |
| Hardened baselines | Reward-bin, rank-bin, and CRC-style baselines can repair the one-state toy, so the toy alone does not prove unique method novelty. |
| Policy mismatch | Behavior-policy residual labels can look safe while deployment-continuation labels fail; residual certificates are policy-specific. |
| No overlap | Unsupported high-reward actions cannot receive nontrivial distribution-free safety certificates from offline support alone. |

Paper use:

```text
These results justify the problem and scope. They should not be oversold as
benchmark dominance.
```

### 2. Synthetic OSRL-Style Strong-Proposer Pilot

Useful assets:

```text
outputs/phase_strong_proposer_pilot_server.json
outputs/phase_strong_proposer_pilot_server.md
outputs/phase_strong_proposer_query_bank_server.npz
```

Key numbers:

| Metric | Value |
|---|---:|
| candidate false rate | 3.24% |
| top-reward selected false rate | 15.99% |
| global candidate CP selected false | 15.17% |
| ACCS-v0 selected false | 0.21% |
| ACCS-v0 yield | 100.00% |

Paper use:

```text
This validates the server pipeline and gives a non-toy bridge, but it remains
synthetic. It is useful for method debugging and motivation, not as the main
benchmark claim.
```

### 3. Official DSRL Direct-OSRL Main Table

Useful assets:

```text
analysis/main_table_protocol.md
analysis/paper_assets/table_main_direct_osrl.csv
analysis/paper_assets/table_main_direct_osrl.md
analysis/paper_assets/table_main_direct_osrl.tex
analysis/experiment_section_draft.md
```

Main paper rows:

| Row | Proposer | Setting | Candidate false | Top false | Global CP R/Y | Reward-bin R/Y | CRC R/Y | ACCS-v0 R/Y |
|---|---|---|---:|---:|---:|---:|---:|---:|
| stability | CAPSIQL 50k | q0.93 | 4.42 | 5.68 | 0.09 / 3.81 | 3.59 / 71.71 | 2.67 / 83.52 | 2.28 / 80.60 |
| high-signal | CPQ 10k | q0.92 | 6.40 | 7.17 | 0.08 / 7.33 | 1.99 / 60.96 | 2.78 / 83.44 | 2.25 / 80.18 |
| stress | COptiDICE 10k | q0.92 | 6.36 | 8.30 | 0.13 / 8.08 | 3.12 / 57.94 | 2.28 / 79.15 | 2.17 / 78.33 |

Interpretation:

```text
The main table supports the central selected-claim audit story on official DSRL
CarCircle with trained safe-RL proposers. Global CP can control risk but often
does so with very low yield; ACCS-v0 preserves about 78-81% yield in the
high-signal rows while keeping selected false certification around 2.2-2.3%.
```

### 4. Residual-Horizon Stress

Useful assets:

```text
outputs/phase_dsrl_horizon_stress_summary.md
analysis/paper_assets/table_dsrl_horizon_stress.csv
```

Key rows:

| Proposer | H | Top false | ACCS-v0 R/Y |
|---|---:|---:|---:|
| CPQ | 20 | 6.24 | 2.26 / 94.82 |
| CPQ | 80 | 7.04 | 3.61 / 80.13 |
| COptiDICE | 20 | 7.35 | 2.13 / 93.00 |
| COptiDICE | 80 | 6.39 | 3.27 / 84.93 |

Interpretation:

```text
The method remains useful when the residual-label horizon changes. The harder
H=80 setting makes global/reward-bin/CRC baselines closer competitors, so this
is stress evidence rather than a blanket dominance claim.
```

### 5. Episode Boundary And Emission-Budget Proxy

Useful assets:

```text
outputs/phase_dsrl_episode_proxy_car_q92_summary.md
outputs/phase_dsrl_episode_capsweep_proxy_car_q92_summary.md
analysis/paper_assets/table_dsrl_episode_proxy_car_q92.csv
analysis/paper_assets/table_dsrl_episode_capsweep_proxy_car_q92.csv
analysis/paper_assets/table_dsrl_episode_capsweep_proxy_car_q92.tex
```

Key results:

| Proposer | Rule | Block R/Y | Episode-proxy F/Y | Issued blocks per episode |
|---|---|---:|---:|---:|
| CPQ | ACCS-v0 | 2.25 / 80.18 | 49.08 / 100.00 | 33.18 |
| CPQ | ACCS-v0 + cap1 | 0.46 / 2.42 | 0.46 / 100.00 | 1.00 |
| CPQ | ACCS-v0 + cap4 | 0.80 / 9.67 | 2.53 / 100.00 | 4.00 |
| CPQ | ACCS-v0 + cap8 | 1.55 / 19.33 | 10.57 / 100.00 | 8.00 |
| COptiDICE | ACCS-v0 | 2.17 / 78.33 | 44.37 / 100.00 | 32.41 |
| COptiDICE | ACCS-v0 + cap1 | 0.69 / 2.42 | 0.69 / 100.00 | 1.00 |
| COptiDICE | ACCS-v0 + cap4 | 0.72 / 9.67 | 2.64 / 100.00 | 4.00 |
| COptiDICE | ACCS-v0 + cap8 | 1.45 / 19.33 | 9.54 / 100.00 | 8.00 |

Interpretation:

```text
The logged episode proxy makes a scope boundary concrete: good action-level
selected-claim risk does not automatically imply episode-level safety. Sparse
emission budgets give a viable risk-allocation route, but this proxy is not a
closed-loop simulator guarantee.
```

### 6. Historical True Closed-Loop First-Cap Audit

Useful assets:

```text
src/run_dsrl_closed_loop_smoke.py
src/run_dsrl_closed_loop_audit.py
src/run_dsrl_closed_loop_fixed_cap_audit.py
outputs/phase_dsrl_closed_loop_fixed_cap_car_100x100_summary.md
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_car_100x100_diagnostic.csv
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_car_100x100.tex
analysis/closed_loop_audit_status.md
```

Historical paper-facing result before the 4090 frontier:

| Proposer | Cap | Audit false/issued | Audit CP90/95 | Test false/issued | Test CP90/95 | Test violation |
|---|---:|---:|---:|---:|---:|---:|
| CPQ | 1 | 1 / 300 | 1.29 / 1.57 | 5 / 300 | 3.07 / 3.47 | 1.67 +/- 1.53 |
| CPQ | 4 | 1 / 300 | 1.29 / 1.57 | 5 / 300 | 3.07 / 3.47 | 1.67 +/- 1.53 |
| CPQ | 8 | 1 / 300 | 1.29 / 1.57 | 5 / 300 | 3.07 / 3.47 | 1.67 +/- 1.53 |
| COptiDICE | 1 | 169 / 300 | 60.13 / 61.15 | 188 / 300 | 66.34 / 67.32 | 62.67 +/- 17.67 |
| COptiDICE | 4 | 169 / 300 | 60.13 / 61.15 | 188 / 300 | 66.34 / 67.32 | 62.67 +/- 17.67 |
| COptiDICE | 8 | 169 / 300 | 60.13 / 61.15 | 188 / 300 | 66.34 / 67.32 | 62.67 +/- 17.67 |

Interpretation:

```text
This was the first clean closed-loop evidence. The first-cap rule is fixed
before audit labels and does not fit a score threshold. CPQ is the positive
case: 5/300 test false issued episodes gives an exact one-sided CP95 upper
bound of 3.47%. COptiDICE is the matched unsafe stress case: 188/300 test false
issued episodes gives CP95 67.32%. It is now superseded in the main text by the
4090 200/200 fixed-cap frontier, but remains a useful historical trace.
```

Older score-threshold closed-loop diagnostics remain useful as traces. The
historical first-cap result above is cleaner than those score-threshold
diagnostics, while the 4090 fixed-cap frontier should now be cited first.

### 7. True Closed-Loop Fixed-Cap Frontier

Useful assets:

```text
scripts/run_closed_loop_frontier_4090.sh
scripts/summarize_closed_loop_frontier_outputs.py
outputs/phase_dsrl_closed_loop_fixed_cap_frontier_200x200_20260630_4090_summary.md
outputs/phase_dsrl_closed_loop_fixed_cap_frontier_drone_200x200_20260630_4090_summary.md
outputs/phase_dsrl_closed_loop_fixed_cap_frontier_all_200x200_20260630_4090_summary.md
outputs/phase_dsrl_closed_loop_fixed_cap_frontier_caps64_200x200_20260630_4090_summary.md
outputs/phase_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090_summary.md
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_frontier_200x200_20260630_4090.csv
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_frontier_drone_200x200_20260630_4090.csv
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_frontier_all_200x200_20260630_4090.csv
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_frontier_caps64_200x200_20260630_4090.csv
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090.csv
outputs/frontier_200x200_20260630_4090_logs/driver_status.tsv
outputs/frontier_drone_200x200_20260630_4090_logs/driver_status.tsv
outputs/frontier_caps64_200x200_20260630_4090_logs/driver_status.tsv
outputs/frontier_capsfull_200x200_20260630_4090_logs/driver_status.tsv
```

Primary 4090 result, 3 seeds x 200 audit / 200 test episodes:

| Env | Proposer | Cap shown | Audit false/issued | Audit CP95 | Test false/issued | Test CP95 | Test violation | Issued steps/ep |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| BallCircle | CPQ | 512 | 0 / 600 | 0.50 | 0 / 600 | 0.50 | 0.00 +/- 0.00 | 200.00 |
| CarCircle | CPQ | 512 | 11 / 600 | 3.02 | 12 / 600 | 3.22 | 2.00 +/- 1.73 | 300.00 |
| DroneCircle | CPQ | 512 | 87 / 600 | 17.08 | 90 / 600 | 17.61 | 15.00 +/- 13.61 | 49.52 |
| BallCircle | COptiDICE | 512 | 533 / 600 | 90.89 | 533 / 600 | 90.89 | 88.83 +/- 9.07 | 200.00 |
| CarCircle | COptiDICE | 512 | 370 / 600 | 64.97 | 365 / 600 | 64.15 | 60.83 +/- 16.83 | 300.00 |
| DroneCircle | COptiDICE | 512 | 587 / 600 | 98.71 | 576 / 600 | 97.23 | 96.00 +/- 4.09 | 271.91 |

Interpretation:

```text
This supersedes the 100/100 first-cap result as the strongest closed-loop
evidence. The pre-registered fixed-cap family was evaluated at caps
64,128,256,512 without fitting a threshold on audit labels. On CPQ CarCircle
and BallCircle, cap512 preserves exact test CP95 below 5% while issuing
certificates for the full 300-step and 200-step episodes. COptiDICE remains a matched unsafe stress
contrast. DroneCircle remains a boundary diagnostic: CPQ improves strongly over
COptiDICE but still has 90/600 test false issued episodes and CP95 17.61%.
```

Paper use:

```text
Main text promotes a fixed-cap risk-yield frontier: CPQ supports full-episode certification on
Car/Ball under exact episode-binomial accounting, while COptiDICE and Drone
show that the audit is not hiding unsafe policies or harder environments.
The appendix keeps the cap 64/128/256/512 saturation table.
```

### 8. True Closed-Loop Tune/Audit/Test Rule Diagnostic

Useful assets:

```text
src/run_dsrl_closed_loop_tuned_rule_audit.py
scripts/run_closed_loop_tuned_rule_4090.sh
scripts/summarize_closed_loop_tuned_rule_outputs.py
outputs/phase_dsrl_closed_loop_tuned_rule_tuned_rule_100x200x200_20260630_4090_summary.md
analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_tuned_rule_100x200x200_20260630_4090.csv
outputs/tuned_rule_100x200x200_20260630_4090_logs/driver_status.tsv
outputs/phase_dsrl_closed_loop_tuned_rule_tuned_rule_drone_conservative_200x300x300_20260630_4090_summary.md
analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_tuned_rule_drone_conservative_200x300x300_20260630_4090.csv
outputs/phase_dsrl_closed_loop_tuned_rule_tuned_rule_drone_medium_200x300x300_20260630_4090_summary.md
analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_tuned_rule_drone_medium_200x300x300_20260630_4090.csv
```

Protocol:

```text
Each checkpoint seed uses independent tune/audit/test online splits
(100/200/200 episodes). The rule family is selected only on the tune split and
then frozen before audit/test reporting. Candidate rules are fixed first caps
and small score-gated windows over all/early/mid steps.
```

Completed 4090 tuned-rule result, 3 seeds:

| Env | Proposer | Tune false/issued | Audit false/issued | Audit CP95 | Test false/issued | Test CP95 | Issued steps/ep |
|---|---|---:|---:|---:|---:|---:|---:|
| BallCircle | CPQ | 0 / 300 | 0 / 600 | 0.50 | 0 / 600 | 0.50 | 200.00 |
| CarCircle | CPQ | 3 / 300 | 4 / 600 | 1.52 | 10 / 600 | 2.81 | 300.00 |
| DroneCircle | CPQ | 16 / 197 | 31 / 397 | 10.39 | 32 / 395 | 10.73 | 17.08 |
| BallCircle | COptiDICE | 233 / 264 | 468 / 530 | 90.53 | 466 / 525 | 90.96 | 69.65 |
| CarCircle | COptiDICE | 54 / 129 | 128 / 292 | 48.81 | 138 / 295 | 51.74 | 7.64 |
| DroneCircle | COptiDICE | 222 / 230 | 461 / 472 | 98.69 | 437 / 455 | 97.43 | 99.61 |

Focused Drone-only follow-ups:

| Run | Proposer | Tune false/issued | Audit false/issued | Audit CP95 | Test false/issued | Test CP95 | Issued steps/ep |
|---|---|---:|---:|---:|---:|---:|---:|
| conservative 200/300/300 | CPQ | 0 / 4 | 4 / 5 | 98.98 | 1 / 4 | 75.14 | 0.01 |
| conservative 200/300/300 | COptiDICE | 119 / 127 | 173 / 186 | 95.82 | 153 / 164 | 96.19 | 2.76 |
| medium 200/300/300 | CPQ | 22 / 388 | 32 / 581 | 7.33 | 54 / 581 | 11.52 | 16.78 |
| medium 200/300/300 | COptiDICE | 242 / 253 | 402 / 420 | 97.21 | 366 / 377 | 98.36 | 1.43 |

Interpretation:

```text
This is useful but not a new main-table upgrade. The tuned rule preserves the
positive CPQ Car/Ball story and keeps COptiDICE as a stress contrast. The broad
tuned run reduces CPQ DroneCircle from the full-cap boundary result of 90/600
test false episodes (CP95 17.61%) to 32/395 (CP95 10.73%), but this is still
above the 5% target and the selected rules vary across seeds. Two Drone-only
follow-ups did not fix the problem: the conservative search barely issued
certificates, and the medium search stayed above 10% CP95. Treat DroneCircle as
a harder-environment boundary diagnostic unless a genuinely new method idea is
introduced.
```

Paper use:

```text
Main-text boundary sentence plus appendix table. Do not replace the fixed-cap
main table with this result.
```

### 9. Broader-Environment Robustness

Useful assets:

```text
analysis/paper_assets/table_dsrl_ball_drone_10k_q92_feasibility.csv
analysis/paper_assets/table_dsrl_ball_drone_10k_q92_feasibility.md
analysis/paper_assets/table_dsrl_coptidice_checkpoint_ball_10k_q92_modelbest_seeds.csv
outputs/phase_dsrl_closed_loop_fixed_cap_ball_matched_100x100_summary.md
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_ball_matched_100x100_diagnostic.csv
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_ball_matched_100x100.tex
outputs/phase_dsrl_closed_loop_fixed_cap_drone_matched_100x100_summary.md
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_drone_matched_100x100_diagnostic.csv
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_drone_matched_100x100.tex
```

Key one-seed feasibility rows:

| Proposer | Env | Candidate false | Top false | ACCS-v0 R/Y |
|---|---|---:|---:|---:|
| CPQ | BallCircle | 6.35 | 5.95 | 1.88 / 85.94 |
| CPQ | DroneCircle | 2.35 | 3.04 | 2.12 / 88.71 |
| COptiDICE | BallCircle | 6.15 | 6.53 | 2.94 / 80.46 |
| COptiDICE | DroneCircle | 2.27 | 3.19 | 2.84 / 98.18 |

Three-seed COptiDICE BallCircle follow-up:

```text
candidate false: 5.15%
top false: 4.85%
global CP: 4.03% / 97.36%
CRC: 2.82% / 91.73%
ACCS-v0: 2.48% / 88.61%
```

Three-seed first-cap closed-loop BallCircle follow-up:

| Proposer | Cap | Audit false/issued | Audit CP90/95 | Test false/issued | Test CP90/95 | Test violation |
|---|---:|---:|---:|---:|---:|---:|
| CPQ | 1 | 0 / 300 | 0.76 / 0.99 | 0 / 300 | 0.76 / 0.99 | 0.00 +/- 0.00 |
| CPQ | 4 | 0 / 300 | 0.76 / 0.99 | 0 / 300 | 0.76 / 0.99 | 0.00 +/- 0.00 |
| CPQ | 8 | 0 / 300 | 0.76 / 0.99 | 0 / 300 | 0.76 / 0.99 | 0.00 +/- 0.00 |
| COptiDICE | 1 | 253 / 300 | 87.01 / 87.69 | 256 / 300 | 87.93 / 88.59 | 85.33 +/- 13.20 |
| COptiDICE | 4 | 253 / 300 | 87.01 / 87.69 | 256 / 300 | 87.93 / 88.59 | 85.33 +/- 13.20 |
| COptiDICE | 8 | 253 / 300 | 87.01 / 87.69 | 256 / 300 | 87.93 / 88.59 | 85.33 +/- 13.20 |

Three-seed first-cap closed-loop DroneCircle diagnostic:

| Proposer | Cap | Audit false/issued | Audit CP90/95 | Test false/issued | Test CP90/95 | Test violation |
|---|---:|---:|---:|---:|---:|---:|
| CPQ | 1 | 45 / 300 | 17.98 / 18.82 | 46 / 300 | 18.34 / 19.18 | 15.33 +/- 8.33 |
| CPQ | 4 | 45 / 300 | 17.98 / 18.82 | 46 / 300 | 18.34 / 19.18 | 15.33 +/- 8.33 |
| CPQ | 8 | 45 / 300 | 17.98 / 18.82 | 46 / 300 | 18.34 / 19.18 | 15.33 +/- 8.33 |
| COptiDICE | 1 | 289 / 300 | 97.65 / 97.93 | 294 / 300 | 98.95 / 99.13 | 98.00 +/- 2.00 |
| COptiDICE | 4 | 289 / 300 | 97.65 / 97.93 | 294 / 300 | 98.95 / 99.13 | 98.00 +/- 2.00 |
| COptiDICE | 8 | 289 / 300 | 97.65 / 97.93 | 294 / 300 | 98.95 / 99.13 | 98.00 +/- 2.00 |

Interpretation:

```text
The direct selected-claim Ball/Drone rows support robustness and feasibility,
not a stronger action-level headline stress row than CarCircle. The true
closed-loop first-cap BallCircle result is stronger: CPQ gives a second
three-seed positive environment with 0/300 test false issued episodes and a
0.99% exact CP95 upper bound, while COptiDICE gives a matched unsafe BallCircle
stress case with 256/300 test false issued episodes and an 88.59% exact CP95
upper bound. The matched DroneCircle audit should be treated as a boundary
diagnostic rather than a third positive environment: COptiDICE is nearly always
unsafe online, and CPQ also has nontrivial residual episode risk with 46/300
test false issued episodes and a 19.18% exact CP95 upper bound.
```

### 10. SafeFQL Availability Check

Useful status as of 2026-06-30/2026-07-01:

```text
arXiv: 2603.15136
project page: https://tau-intelligence.com/safe-fql/
public GitHub: https://github.com/tau-intelligence/safe-fql.git
previous observed commit on 2026-06-24: 5774862564432bbfcfd16d511c986001978108e5
latest observed HEAD: 106cef25ef8403b3384092e30201973a28f3dfae
local shallow clone: external/SafeFQL
clone contents: Readme.md only
```

Interpretation:

```text
SafeFQL is strategically important prior work and should be positioned in the
paper. The public repository has changed commit since the first check, but the
latest shallow clone is still README-only and does not provide runnable
training, checkpoint, evaluator, or dependency files. A fair direct experiment
is still blocked on runnable artifacts; do not create an approximate SafeFQL
surrogate unless it can be made fair and clearly labeled.
```

### 11. Off-Policy Query-Shift Toy

Useful assets:

```text
src/toy_offpolicy_shift.py
outputs/toy_offpolicy_shift.csv
outputs/toy_offpolicy_shift_summary.md
figures/figure4_offpolicy_shift.pdf
figures/figure4_offpolicy_shift.png
```

Interpretation:

```text
This is a local method-direction diagnostic for the weighted/off-policy theorem
route, not a replacement for the trained DSRL evidence. It now supports a
single main-text diagnostic paragraph plus the appendix table. The audit law P is
uniform over a selected-query score x, while the deployment law Q tilts toward
high-reward/high-risk x with density a*x^(a-1). At strong shift a=8, the
unweighted P-audit chooses tau=0.895 and has 33.90% deployment false
certification at 41.19% yield. Known-ratio weighting chooses tau=0.855 and
tracks the oracle Q-audit at 4.45% deployment false certification with 28.49%
yield. A hard support cap at the unsafe boundary gives 0% false certification
with 27.23% yield. This supports the claim that off-policy deployment query
laws require explicit weighting/support accounting and that the cost appears as
effective sample size or abstention.
```

---

## Useful Negative Or Diagnostic Results

| Diagnostic | What was learned | Paper use |
|---|---|---|
| Old DSRL endpoint | `data.offline-saferl.org` endpoint was stale/unreachable. Current Hugging Face HDF5 files work. | Environment note only. |
| Official HDF5 logged-neighbor pilot | Data loading works, but logged-neighbor query law does not create a useful selected-risk gap. | Do not promote. |
| DSRL env self-generated query-bank pilots | Simulator plumbing works, but selection gaps and auditor behavior were unstable. | Do not promote. |
| Weighted-BC multi-head proposer | Training/evaluator path works, but the selection gap is weak. | Keep as scaffold only. |
| CPQ/COptiDICE Ball/Drone smokes | Confirmed environment and evaluator compatibility. | Reproducibility, not paper evidence. |
| DroneCircle first-cap closed-loop audit | COptiDICE is almost always unsafe online; CPQ also has residual episode risk above the 5% target. | Boundary/appendix diagnostic, not a main positive claim. |

---

## Claim Boundaries

Supported:

| Claim | Current support |
|---|---|
| Marginal calibration before selection does not imply post-selection certificate control. | Exact toy, synthetic pilot, official DSRL main table. |
| ACCS-v0 controls selected-claim risk at useful yield in trained CarCircle rows. | CAPSIQL/CPQ/COptiDICE direct-OSRL main table. |
| Residual labels are policy-specific and support-sensitive. | Policy-mismatch and no-overlap diagnostics plus theory spine. |
| Off-policy deployment query laws require weighting or support checks. | Weighted off-policy theorem spine plus local shift diagnostic: at a=8, unweighted P-audit has 33.90% risk / 41.19% yield under Q, while known-ratio weighting has 4.45% / 28.49% and support cap has 0% / 27.23%. |
| Episode-level claims need separate emission budgeting or closed-loop audit. | Logged episode proxy, 100/100 first-cap audit, and 4090 200/200 fixed-cap frontier. |
| A pre-registered sparse emission rule can be audited online with practical episode counts. | 4090 fixed-cap frontier: CPQ cap512 has CarCircle 12/600 test false with CP95 3.22% and BallCircle 0/600 with CP95 0.50%, while saturating full episodes. |
| The fixed-cap closed-loop contrast is not CarCircle-only. | BallCircle is a second positive CPQ environment; COptiDICE fails on Car/Ball/Drone; DroneCircle exposes harder-environment residual risk with CPQ 90/600 test false and CP95 17.61%. |

Not yet supported:

| Claim | Missing evidence |
|---|---|
| ACCS dominates every strong selective baseline. | False in the toy; baselines remain close in some stress settings. |
| The method gives arbitrary closed-loop safety. | Only pre-registered sparse fixed-cap closed-loop audits are supported. |
| SafeFQL direct comparison. | Runnable code/checkpoints or a fair reimplementation. |
| Broad arbitrary-environment closed-loop generality. | Fixed-cap audit has positive CPQ cases on CarCircle and BallCircle, but DroneCircle is a boundary diagnostic rather than a positive 5% episode-risk result. |
| Broad sequential distribution-shift robustness. | A server-scale shift audit or a formal deployment weighting/support contract beyond the local off-policy toy. |

---

## Reproducibility Pointers

Main server paths:

```text
/workspace/thymic_project/paper/aaai_2
/home/ccj/workspace_1/aaai_2
```

Core environment:

```text
WANDB_MODE=offline
DSRL_DATASET_DIR=/workspace/thymic_project/paper/aaai_2/data/dsrl
PYTHONPATH=/workspace/thymic_project/paper/aaai_2/external/OSRL:/workspace/thymic_project/paper/aaai_2/src
```

4090 frontier environment:

```text
conda activate aaai2
PYTHONPATH=/home/ccj/workspace_1/aaai_2/src:/home/ccj/workspace_1/aaai_2/external/OSRL
RUN_ID=frontier_200x200_20260630_4090 bash scripts/run_closed_loop_frontier_4090.sh
RUN_ID=frontier_drone_200x200_20260630_4090 ENV_SHORTS=drone bash scripts/run_closed_loop_frontier_4090.sh
```

Useful logs and detailed chronology:

```text
analysis/reproduction_log.md
analysis/claim_evidence_map.md
analysis/paper_assets/README.md
```
