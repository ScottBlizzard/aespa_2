# Closed-Loop Episode Audit Status

Updated: 2026-06-30

## Status

The fourth-step closed-loop branch now has matched three-seed 200/200
pre-registered fixed-cap frontier diagnostics for CPQ and COptiDICE on
CarCircle, BallCircle, and DroneCircle. CarCircle/BallCircle are positive
paper-facing environments for CPQ up to full-episode saturation; DroneCircle is a harder boundary
diagnostic. The first tune/audit/test selected-rule extension has also been run
as a diagnostic. Eight local scripts support it:

```text
src/run_dsrl_closed_loop_smoke.py
src/run_dsrl_closed_loop_audit.py
src/run_dsrl_closed_loop_fixed_cap_audit.py
src/run_dsrl_closed_loop_tuned_rule_audit.py
scripts/run_closed_loop_frontier_4090.sh
scripts/summarize_closed_loop_frontier_outputs.py
scripts/run_closed_loop_tuned_rule_4090.sh
scripts/summarize_closed_loop_tuned_rule_outputs.py
```

The smoke script verifies online simulator rollout and reward/cost accounting.
The audit script fits a small online rule family on audit episodes and evaluates
episode-budgeted certificate emission on independent test episodes.

## Current Outputs

```text
outputs/phase_dsrl_closed_loop_smoke_cpq_car_seed20260624_server.json
outputs/phase_dsrl_closed_loop_smoke_coptidice_car_seed20260624_server.json
outputs/phase_dsrl_closed_loop_audit_cpq_car_seed20260624_30x30_server.json
outputs/phase_dsrl_closed_loop_audit_coptidice_car_seed20260624_30x30_server.json
outputs/phase_dsrl_closed_loop_audit_car_30x30_summary.md
analysis/paper_assets/table_dsrl_closed_loop_audit_car_30x30_diagnostic.csv
outputs/phase_dsrl_closed_loop_audit_cpq_car_100x100_summary.md
analysis/paper_assets/table_dsrl_closed_loop_audit_cpq_car_100x100_diagnostic.csv
outputs/phase_dsrl_closed_loop_audit_coptidice_car_100x100_summary.md
analysis/paper_assets/table_dsrl_closed_loop_audit_coptidice_car_100x100_diagnostic.csv
outputs/phase_dsrl_closed_loop_fixed_cap_car_100x100_summary.md
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_car_100x100_diagnostic.csv
outputs/phase_dsrl_closed_loop_fixed_cap_ball_matched_100x100_summary.md
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_ball_matched_100x100_diagnostic.csv
outputs/phase_dsrl_closed_loop_fixed_cap_drone_matched_100x100_summary.md
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_drone_matched_100x100_diagnostic.csv
outputs/phase_dsrl_closed_loop_fixed_cap_frontier_all_200x200_20260630_4090_summary.md
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_frontier_all_200x200_20260630_4090.csv
outputs/phase_dsrl_closed_loop_fixed_cap_frontier_caps64_200x200_20260630_4090_summary.md
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_frontier_caps64_200x200_20260630_4090.csv
outputs/phase_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090_summary.md
analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090.csv
outputs/phase_dsrl_closed_loop_tuned_rule_tuned_rule_100x200x200_20260630_4090_summary.md
analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_tuned_rule_100x200x200_20260630_4090.csv
outputs/phase_dsrl_closed_loop_tuned_rule_tuned_rule_drone_conservative_200x300x300_20260630_4090_summary.md
analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_tuned_rule_drone_conservative_200x300x300_20260630_4090.csv
outputs/phase_dsrl_closed_loop_tuned_rule_tuned_rule_drone_medium_200x300x300_20260630_4090_summary.md
analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_tuned_rule_drone_medium_200x300x300_20260630_4090.csv
outputs/frontier_200x200_20260630_4090_logs/driver_status.tsv
outputs/frontier_drone_200x200_20260630_4090_logs/driver_status.tsv
outputs/frontier_caps64_200x200_20260630_4090_logs/driver_status.tsv
outputs/frontier_capsfull_200x200_20260630_4090_logs/driver_status.tsv
outputs/tuned_rule_100x200x200_20260630_4090_logs/driver_status.tsv
outputs/tuned_rule_drone_conservative_200x300x300_20260630_4090_logs/driver_status.tsv
outputs/tuned_rule_drone_medium_200x300x300_20260630_4090_logs/driver_status.tsv
```

## 4090 Fixed-Cap 200/200 Full-Cap Frontier

This is the cleanest current closed-loop evidence. The rule family is fixed
before audit labels: issue certificates for the first cap policy steps in every
online episode, with caps 64,128,256,512. No score threshold is fit on audit
labels.

Values are aggregated across seeds 20260624/20260625/20260626. CP bounds are
one-sided exact binomial upper bounds.

| Env | Proposer | Cap shown | Audit false/issued | Audit CP95 | Test false/issued | Test CP95 | Test violation | Issued steps/ep |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| BallCircle | CPQ | 512 | 0 / 600 | 0.0050 | 0 / 600 | 0.0050 | 0.0000 +/- 0.0000 | 200.00 |
| CarCircle | CPQ | 512 | 11 / 600 | 0.0302 | 12 / 600 | 0.0322 | 0.0200 +/- 0.0173 | 300.00 |
| DroneCircle | CPQ | 512 | 87 / 600 | 0.1708 | 90 / 600 | 0.1761 | 0.1500 +/- 0.1361 | 49.52 |
| BallCircle | COptiDICE | 512 | 533 / 600 | 0.9089 | 533 / 600 | 0.9089 | 0.8883 +/- 0.0907 | 200.00 |
| CarCircle | COptiDICE | 512 | 370 / 600 | 0.6497 | 365 / 600 | 0.6415 | 0.6083 +/- 0.1683 | 300.00 |
| DroneCircle | COptiDICE | 512 | 587 / 600 | 0.9871 | 576 / 600 | 0.9723 | 0.9600 +/- 0.0409 | 271.91 |

Across caps 64,128,256,512, the false issued episode counts remain stable for
these fixed first-step rules, while issued steps per episode scale until episode
termination or lack of certifiable steps. The paper-facing conclusion is that
CPQ supports full-episode certification on CarCircle and BallCircle under exact
closed-loop episode accounting. DroneCircle is not a positive 5% case; it is a
boundary diagnostic.

## Tune/Audit/Test 100/200/200 Selected-Rule Diagnostic

This is the first higher-upside extension beyond fixed first-cap rules. Each
checkpoint seed uses a tune split to select from a small rule family, then
freezes the selected rule before audit/test reporting. Candidate rules include
fixed first caps and score-gated all/early/mid windows. This is not currently a
main-paper replacement because it is less clean than the fixed-cap table and
does not solve DroneCircle.

Values are aggregated across seeds 20260624/20260625/20260626.

| Env | Proposer | Tune false/issued | Audit false/issued | Audit CP95 | Test false/issued | Test CP95 | Issued steps/ep |
|---|---|---:|---:|---:|---:|---:|---:|
| BallCircle | CPQ | 0 / 300 | 0 / 600 | 0.0050 | 0 / 600 | 0.0050 | 200.00 |
| CarCircle | CPQ | 3 / 300 | 4 / 600 | 0.0152 | 10 / 600 | 0.0281 | 300.00 |
| DroneCircle | CPQ | 16 / 197 | 31 / 397 | 0.1039 | 32 / 395 | 0.1073 | 17.08 |
| BallCircle | COptiDICE | 233 / 264 | 468 / 530 | 0.9053 | 466 / 525 | 0.9096 | 69.65 |
| CarCircle | COptiDICE | 54 / 129 | 128 / 292 | 0.4881 | 138 / 295 | 0.5174 | 7.64 |
| DroneCircle | COptiDICE | 222 / 230 | 461 / 472 | 0.9869 | 437 / 455 | 0.9743 | 99.61 |

The useful signal is the CPQ Drone reduction: fixed-cap cap512 had 90/600 test
false issued episodes with exact CP95 17.61%, while the tuned diagnostic has
32/395 and CP95 10.73%. That is meaningful progress but not enough to promote:
the selected Drone rules are seed-unstable and still above the 5% episode-risk
target.

Two focused Drone-only follow-ups do not change this verdict:

| Run | Proposer | Test false/issued | Test CP95 | Issued steps/ep | Read |
|---|---|---:|---:|---:|---|
| conservative 200/300/300 | CPQ | 1 / 4 | 0.7514 | 0.01 | too sparse |
| conservative 200/300/300 | COptiDICE | 153 / 164 | 0.9619 | 2.76 | unsafe stress |
| medium 200/300/300 | CPQ | 54 / 581 | 0.1152 | 16.78 | above target |
| medium 200/300/300 | COptiDICE | 366 / 377 | 0.9836 | 1.43 | unsafe stress |

The practical conclusion is to stop Drone threshold/cap-only sweeps for now.
DroneCircle should remain a boundary diagnostic unless there is a new
method-level idea.

## Historical First-Cap 100/100 Fixed-Rule Audit

This was the first clean closed-loop evidence before the 4090 frontier. The
rule is fixed before audit labels: issue certificates for the first cap policy
steps in every online episode. No score threshold is fit on audit labels.

Values are mean +/- std across seeds 20260624/20260625/20260626.

| Proposer | Cap | Audit false/issued | Audit CP90/95 | Test false/issued | Test CP90/95 | Test violation |
|---|---:|---:|---:|---:|---:|---:|
| CPQ | 1 | 1 / 300 | 0.0129 / 0.0157 | 5 / 300 | 0.0307 / 0.0347 | 0.0167 +/- 0.0153 |
| CPQ | 4 | 1 / 300 | 0.0129 / 0.0157 | 5 / 300 | 0.0307 / 0.0347 | 0.0167 +/- 0.0153 |
| CPQ | 8 | 1 / 300 | 0.0129 / 0.0157 | 5 / 300 | 0.0307 / 0.0347 | 0.0167 +/- 0.0153 |
| COptiDICE | 1 | 169 / 300 | 0.6013 / 0.6115 | 188 / 300 | 0.6634 / 0.6732 | 0.6267 +/- 0.1767 |
| COptiDICE | 4 | 169 / 300 | 0.6013 / 0.6115 | 188 / 300 | 0.6634 / 0.6732 | 0.6267 +/- 0.1767 |
| COptiDICE | 8 | 169 / 300 | 0.6013 / 0.6115 | 188 / 300 | 0.6634 / 0.6732 | 0.6267 +/- 0.1767 |

This remains a useful historical trace because it has no adaptive
threshold-selection penalty, but the 4090 200/200 frontier above should now be
cited first.

## BallCircle Matched First-Cap 100/100 Fixed-Rule Audit

This is the broader-environment follow-up under the same rule and accounting.

Values are mean +/- std across seeds 20260624/20260625/20260626.

| Proposer | Cap | Audit false/issued | Audit CP90/95 | Test false/issued | Test CP90/95 | Test violation |
|---|---:|---:|---:|---:|---:|---:|
| CPQ | 1 | 0 / 300 | 0.0076 / 0.0099 | 0 / 300 | 0.0076 / 0.0099 | 0.0000 +/- 0.0000 |
| CPQ | 4 | 0 / 300 | 0.0076 / 0.0099 | 0 / 300 | 0.0076 / 0.0099 | 0.0000 +/- 0.0000 |
| CPQ | 8 | 0 / 300 | 0.0076 / 0.0099 | 0 / 300 | 0.0076 / 0.0099 | 0.0000 +/- 0.0000 |
| COptiDICE | 1 | 253 / 300 | 0.8701 / 0.8769 | 256 / 300 | 0.8793 / 0.8859 | 0.8533 +/- 0.1320 |
| COptiDICE | 4 | 253 / 300 | 0.8701 / 0.8769 | 256 / 300 | 0.8793 / 0.8859 | 0.8533 +/- 0.1320 |
| COptiDICE | 8 | 253 / 300 | 0.8701 / 0.8769 | 256 / 300 | 0.8793 / 0.8859 | 0.8533 +/- 0.1320 |

This materially strengthens the closed-loop story because the same fixed-rule
audit now has a second three-seed positive CPQ environment and a second matched
unsafe COptiDICE stress environment.

## DroneCircle Matched First-Cap 100/100 Fixed-Rule Diagnostic

This is the harder-environment boundary follow-up under the same rule and
accounting. It should not be promoted as a third positive closed-loop result.

Values are mean +/- std across seeds 20260624/20260625/20260626.

| Proposer | Cap | Audit false/issued | Audit CP90/95 | Test false/issued | Test CP90/95 | Test violation |
|---|---:|---:|---:|---:|---:|---:|
| CPQ | 1 | 45 / 300 | 0.1798 / 0.1882 | 46 / 300 | 0.1834 / 0.1918 | 0.1533 +/- 0.0833 |
| CPQ | 4 | 45 / 300 | 0.1798 / 0.1882 | 46 / 300 | 0.1834 / 0.1918 | 0.1533 +/- 0.0833 |
| CPQ | 8 | 45 / 300 | 0.1798 / 0.1882 | 46 / 300 | 0.1834 / 0.1918 | 0.1533 +/- 0.0833 |
| COptiDICE | 1 | 289 / 300 | 0.9765 / 0.9793 | 294 / 300 | 0.9895 / 0.9913 | 0.9800 +/- 0.0200 |
| COptiDICE | 4 | 289 / 300 | 0.9765 / 0.9793 | 294 / 300 | 0.9895 / 0.9913 | 0.9800 +/- 0.0200 |
| COptiDICE | 8 | 289 / 300 | 0.9765 / 0.9793 | 294 / 300 | 0.9895 / 0.9913 | 0.9800 +/- 0.0200 |

The diagnostic is still useful: it shows the same audit route exposes residual
episode risk when the positive proposer/environment pair is not sufficiently
safe online.

## Score-Threshold 100/100 Diagnostic

Values are mean +/- std across seeds 20260624/20260625/20260626.

| Proposer | Cap | Audit false/issued | Audit CP90/95 | Test false/issued | Test CP90/95 | Test violation |
|---|---:|---:|---:|---:|---:|---:|
| CPQ | 1 | 4 / 300 | 0.0265 / 0.0303 | 7 / 300 | 0.0389 / 0.0434 | 0.0233 +/- 0.0321 |
| CPQ | 4 | 4 / 300 | 0.0265 / 0.0303 | 7 / 300 | 0.0389 / 0.0434 | 0.0233 +/- 0.0321 |
| CPQ | 8 | 4 / 300 | 0.0265 / 0.0303 | 7 / 300 | 0.0389 / 0.0434 | 0.0233 +/- 0.0321 |

This older diagnostic fits a score threshold on audit episodes and is therefore
less clean than the historical first-cap audit above. Keep it as an auxiliary
trace.

## COptiDICE Three-Seed 100/100 Stress Contrast

Values are mean +/- std across seeds 20260624/20260625/20260626.

| Proposer | Cap | Audit false/issued | Audit CP90/95 | Test false/issued | Test CP90/95 | Test violation |
|---|---:|---:|---:|---:|---:|---:|
| COptiDICE | 1 | 142 / 238 | 0.6388 / 0.6499 | 131 / 231 | 0.6105 / 0.6220 | 0.6167 +/- 0.1674 |
| COptiDICE | 4 | 142 / 238 | 0.6388 / 0.6499 | 131 / 231 | 0.6105 / 0.6220 | 0.6167 +/- 0.1674 |
| COptiDICE | 8 | 142 / 238 | 0.6388 / 0.6499 | 131 / 231 | 0.6105 / 0.6220 | 0.6167 +/- 0.1674 |

This is the matched unsafe closed-loop contrast under the score-threshold
diagnostic. The historical first-cap audit above is cleaner and should be cited
before this score-threshold diagnostic, while the 4090 fixed-cap frontier
should be cited before both.

## Three-Seed 30/30 Diagnostic

Values are mean +/- std across seeds 20260624/20260625/20260626.

| Proposer | Cap | Audit false/issued | Audit CP90 upper | Test false/issued | Test CP90 upper | Test violation |
|---|---:|---:|---:|---:|---:|---:|
| CPQ | 1 | 1 / 90 | 0.0425 | 0 / 90 | 0.0253 | 0.00 +/- 0.00 |
| CPQ | 4 | 1 / 90 | 0.0425 | 0 / 90 | 0.0253 | 0.00 +/- 0.00 |
| CPQ | 8 | 1 / 90 | 0.0425 | 0 / 90 | 0.0253 | 0.00 +/- 0.00 |
| COptiDICE | 1 | 48 / 82 | 0.6589 | 48 / 78 | 0.6894 | 0.63 +/- 0.17 |
| COptiDICE | 4 | 48 / 82 | 0.6589 | 48 / 78 | 0.6894 | 0.63 +/- 0.17 |
| COptiDICE | 8 | 48 / 82 | 0.6589 | 48 / 78 | 0.6894 | 0.63 +/- 0.17 |

## First Single-Seed Diagnostic

| Proposer | Test cost | Test violation | Cap | Test ep F/Y | Test block R/Y |
|---|---:|---:|---:|---:|---:|
| CPQ | 0.00 | 0.00 | 1 | 0.00 / 1.00 | 0.00 / 0.0033 |
| CPQ | 0.00 | 0.00 | 4 | 0.00 / 1.00 | 0.00 / 0.0133 |
| CPQ | 0.00 | 0.00 | 8 | 0.00 / 1.00 | 0.00 / 0.0267 |
| COptiDICE | 43.17 | 0.83 | 1 | 0.83 / 1.00 | 0.83 / 0.0033 |
| COptiDICE | 43.17 | 0.83 | 4 | 0.83 / 1.00 | 0.84 / 0.0132 |
| COptiDICE | 43.17 | 0.83 | 8 | 0.83 / 1.00 | 0.83 / 0.0267 |

## Interpretation

This is no longer just plumbing. The 30/30 branch was the successful smoke and
diagnostic pass; the 100/100 branch established the first clean fixed-rule
closed-loop route; the 4090 200/200 branch is the current paper-facing
fixed-cap frontier.

The useful signal is sharp:

```text
CPQ model_best is an online safe-policy positive case across three seeds on
CarCircle and BallCircle.
COptiDICE model_best is an online unsafe-policy stress case across three seeds
on CarCircle, BallCircle, and DroneCircle.
DroneCircle is a hard-environment boundary case where CPQ no longer meets the
5% episode-risk target under the fixed-cap rule.
```

The large threshold-family episode-UCB rule is not valid at the current episode
counts because adaptive threshold selection consumes too much finite-sample
budget. The pre-registered fixed-cap rule avoids this problem: after
aggregating the three CPQ 4090 200/200 splits, cap512 has 12/600 false issued
test episodes on CarCircle, with exact CP95 3.22%, and 0/600 on BallCircle,
with exact CP95 0.50%. The matched COptiDICE stress rows have 365/600
CarCircle and 533/600 BallCircle false issued test episodes. The matched
DroneCircle diagnostic is not a positive result: CPQ has 90/600 false issued
test episodes with exact CP95 17.61%, while COptiDICE has 576/600 with exact
CP95 97.23%.

## Next Experiment

The next high-upside step is not more identical fixed-cap frontier runs, and it
is not another Drone threshold/cap sweep. The 4090 frontier is already
integrated into the AAAI paper and appendix, and the latest paper/evidence QA
keeps the fixed-cap Car/Ball result as the main closed-loop positive evidence.
The tuned-rule diagnostics now belong in the appendix as diagnostic evidence,
not as a replacement for the main fixed-cap table.

```text
Keep CPQ as the positive closed-loop case and COptiDICE as the stress case.
Keep DroneCircle as boundary evidence.
Do not promote tuned-rule diagnostics unless a new method idea reaches test
CP95 below 5% with nontrivial issued episodes.
Do not launch another 4090 batch until the experiment has a method-level
addition such as support/off-policy weighting, shift-triggered abstention, or a
new pre-registered risk-allocation rule.
```

CPQ stays below the 5% episode-risk target on CarCircle and BallCircle in the
three-seed 200/200 fixed-cap frontier, so it is the right positive closed-loop
case. COptiDICE stays unsafe online in the matched diagnostic, so it is a
useful contrast showing that logged action-certificate success does not imply
trajectory safety for every proposer.

The fixed-rule theory route is now raised in the main paper as an exact
fixed-emission corollary. The remaining theory-sensitive experiment is a
possible support/off-policy shift diagnostic that makes the query-law and
support assumptions operational. It should start locally and move to 4090 only
after the diagnostic has a clear protocol and expected paper-facing claim.
