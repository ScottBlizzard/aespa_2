# Claim-Evidence Map

> **Last updated**: 2026-07-01
> **Scope**: AAAI_2 full-draft claim audit.
> **Rule**: every major claim must point to a theorem, table, figure, canonical server output, or be weakened.
> **Reviewer-facing audit**: `analysis/reviewer_claim_audit_20260701.md`.

---

## Abstract / Introduction Claims

| Claim | Required evidence | Status |
|---|---|---|
| Learned cost/feasibility estimates are not calibrated deployment certificates. | Exact toy plus synthetic OSRL-style server pilot showing low candidate false rate but high selected false rate; official DSRL trained CAPSIQL checkpoint pilot. | local toy + synthetic server pilot supported; trained DSRL CAPSIQL three-seed result supported |
| Ordinary marginal conformal does not control issued-claim risk after action selection. | `outputs/toy_selection_failure_hardened.csv`; TikZ Figure 1 in `aaai2027/tikz_figures.tex`; `outputs/phase_strong_proposer_pilot_server.json`. | local toy + synthetic server pilot supported; main-paper figure uses LaTeX/TikZ source |
| ACCS targets false certification among issued claims. | ACCS-v0 finite-rule auditor in `src/selective_auditor.py`, support+safety pilot in `src/run_strong_proposer_pilot.py`, finite-rule theorem spine in `theory_proofs.md`, and theorem block in `aaai2027/paper.tex`. | local toy + synthetic server pilot supported; paper theorem statement inserted |
| The exact toy is not enough to prove unique ACCS method novelty. | `outputs/toy_selection_failure_hardened.csv`: reward-bin UCB, rank-bin UCB, and CRC-style baselines also repair the toy. | local toy supported |
| Residual-cost certificates are policy-specific. | `outputs/toy_policy_mismatch.csv`; local diagnostic figure asset. | local toy supported; discussed as scope evidence rather than a main figure |
| No support implies abstention is necessary. | `outputs/toy_no_overlap.csv`; local diagnostic figure asset; two-CMDP theorem spine in `theory_proofs.md`, and no-overlap proposition in `aaai2027/paper.tex`. | local toy supported; paper proposition inserted |
| Strong constraint-adaptive policies still need finite-data auditing. | CAPSIQL/CPQ/COptiDICE checkpoints vs global CP/reward-bin/CRC/ACCS on the same fixed query bank. | frozen main-table protocol completed in `analysis/main_table_protocol.md`; CAPSIQL 50k, CPQ 10k, and COptiDICE 10k three-seed results completed |
| The selected-claim audit pattern is not unique to CarCircle. | Trained CPQ/COptiDICE feasibility on BallCircle/DroneCircle plus three-seed COptiDICE BallCircle follow-up and 4090 fixed-cap closed-loop frontier. | robustness evidence supported; fixed-cap CPQ BallCircle has 0/600 test false with exact CP95 0.50% at full cap, while COptiDICE BallCircle has 533/600 test false with CP95 90.89% |
| Global candidate CP is not the practical solution in the trained-proposer rows. | `analysis/paper_assets/table_main_direct_osrl.md`: global CP has low risk but only about 3.8-8.1% yield. | supported by main-table asset |
| ACCS-v0 controls selected-claim risk at useful yield in high-signal trained-proposer rows. | `table_main_direct_osrl.md`: CPQ q0.92 has 7.17% top false and ACCS 2.25%/80.18%; COptiDICE q0.92 has 8.30% top false and ACCS 2.17%/78.33%. | supported by main-table asset |
| The selected-claim audit remains useful under residual-horizon changes. | `outputs/phase_dsrl_horizon_stress_summary.md`; `analysis/paper_assets/table_dsrl_horizon_stress.csv`: CPQ/COptiDICE q0.92 at H=20 and H=80 across three seeds. | supported for CarCircle residual-label stress; not episode-level safety |
| SafeFQL is prior work, but does not close selection-aware moving-budget auditing. | SafeFQL paper/project/GitHub check updated on 2026-06-30/2026-07-01; arXiv 2603.15136 describes conformal calibration of a learned safety boundary, but the public GitHub repository HEAD `106cef25ef8403b3384092e30201973a28f3dfae` still shallow-clones as README-only with no runnable comparator code/checkpoints. | limitation documented; direct comparison pending runnable code/checkpoints |
| Horizon-level / episode-level safety is a separate boundary from selected action certification. | `outputs/phase_dsrl_episode_proxy_car_q92_summary.md`; `analysis/paper_assets/table_dsrl_episode_proxy_car_q92.csv`; pre-registered first-cap 100/100 closed-loop diagnostics; 4090 fixed-cap 200/200 frontier; appendix Tables S2-S5 in `aaai2027/appendix.tex`. | supported as boundary evidence; fixed-cap CPQ is positive on Car/Ball, COptiDICE stress contrasts fail on all three environments, and DroneCircle shows harder-environment residual risk |
| Explicit certificate-emission budgeting is a formal route to episode-level risk allocation. | Episode-budgeted selective-risk theorem plus exact fixed-emission corollary in `theory_proofs.md` and `aaai2027/paper.tex`; `outputs/phase_dsrl_episode_capsweep_proxy_car_q92_summary.md`; `analysis/paper_assets/table_dsrl_episode_capsweep_proxy_car_q92.csv`; `analysis/paper_assets/table_dsrl_episode_capsweep_proxy_car_q92.tex`; `outputs/phase_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090_summary.md`; `outputs/phase_dsrl_closed_loop_tuned_rule_tuned_rule_100x200x200_20260630_4090_summary.md`; focused Drone tuned-rule summaries. | theorem/corollary + logged proxy + 4090 fixed-cap frontier supported; CPQ cap512/full episode passes exact test CP95 <5% on Car/Ball; tune/audit/test selected rules are diagnostics and did not produce a third positive Drone result |
| The true closed-loop branch is technically runnable and exposes proposer-level trajectory differences. | `analysis/closed_loop_audit_status.md`; `src/run_dsrl_closed_loop_smoke.py`; `src/run_dsrl_closed_loop_audit.py`; `src/run_dsrl_closed_loop_fixed_cap_audit.py`; `src/run_dsrl_closed_loop_tuned_rule_audit.py`; `scripts/run_closed_loop_frontier_4090.sh`; `scripts/run_closed_loop_tuned_rule_4090.sh`; `scripts/summarize_closed_loop_frontier_outputs.py`; `scripts/summarize_closed_loop_tuned_rule_outputs.py`; `outputs/phase_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090_summary.md`; tuned-rule summaries; main Table 2 in `aaai2027/paper.tex`; appendix Tables S3-S4 in `aaai2027/appendix.tex`. | 4090 fixed-cap frontier: CPQ cap512 CarCircle test 12/600 with CP95 3.22%, BallCircle 0/600 with CP95 0.50%, DroneCircle 90/600 with CP95 17.61%; broad tuned-rule diagnostic reduces CPQ Drone to 32/395 with CP95 10.73%, but conservative/medium follow-ups fail to cross 5%; COptiDICE remains unsafe |
| Broad sequential distribution shift can be handled by the current protocol. | server-scale shift/off-policy audit or a formal deployment weighting/support contract beyond the local toy. | unsupported as a broad claim; tracked in `NEXT_STEPS.md` |
| Off-policy deployment query laws require weighting or support checks. | polished weighted selective-risk theorem in `theory_proofs.md`; local shift diagnostic in `src/toy_offpolicy_shift.py`; `outputs/toy_offpolicy_shift.csv` shows unweighted P-audit failing under shifted Q while known-ratio/support-capped rules control risk with yield/ESS cost; appendix Table 8 records the compact diagnostic. | supported as a diagnostic and promoted to one main-text paragraph, not as a broad benchmark claim |

---

## Reviewer Questions

| Question | Planned answer | Status |
|---|---|---|
| Is this just conformal prediction plus safe RL? | Reframe as calibration after action selection; ordinary conformal is a baseline expected to fail. | conceptual |
| Did CAPS already solve this? | CAPS filters actions; ACCS audits false certification after CAPS-style action selection. The key comparison is CAPSIQL/CPQ/COptiDICE checkpoint alone vs post-selection auditors on the same query bank. | CAPSIQL, CPQ, and COptiDICE checkpoint pilots completed across three seeds |
| Did SafeFQL already solve this? | SafeFQL calibrates a learned safety boundary; ACCS targets selected-claim risk under candidate/budget queries. The public repository re-checked on 2026-06-30/2026-07-01 still has no runnable comparator code/checkpoints. | limitation documented; direct comparison pending runnable artifacts |
| Why action-conditioned instead of global conformal? | The main issue is selection-aware false certification under a fixed deployment query law; global CP is reported and often controls only by collapsing yield. | addressed by main DSRL table |
| Does action-level coverage imply safe trajectories? | No; the paper explicitly separates action claims, logged episode proxies, and true closed-loop fixed-cap audits. | theory draft + logged episode-block proxy + 4090 fixed-cap closed-loop table + appendix |
| Are groups tuned on test data? | Protocol freeze: groups fixed before test; ACCS-v0 uses independent audit blocks. | locally addressed |
| Is abstention hiding failure? | Report risk with yield and include rejection/failure rows rather than only positive cases. | addressed in Table 1, episode-proxy/cap rows, Table 2, and tuned-rule/Drone diagnostics |
| Are baselines strong enough? | Local toy includes global/group, selected-block, reward-bin, rank-bin, Bonferroni, CRC-style, ACCS-v0, and oracle; first server pilot includes global candidate CP, reward-bin, rank-bin, CRC-style, ACCS-v0, and oracle; direct OSRL main table includes global CP, reward-bin, CRC-style, and ACCS-v0 for CAPSIQL/CPQ/COptiDICE. | addressed for first main table; SafeFQL/broader environments optional |
| Are negative Drone/tuned-rule results just failed experiments? | Use them as boundary evidence: CPQ Drone improves from fixed cap to tuned-rule but still misses 5%, so the paper rejects a positive Drone claim instead of hiding the result. | addressed in main diagnostic sentence and appendix |
| What if audit and deployment query laws differ? | State that the audit must be rerun or justified by weighting/support assumptions; local off-policy shift toy gives the failure and repair pattern. | addressed as diagnostic; server-scale shift robustness remains a NEXT item |
| Is the first server pilot protocol frozen? | `analysis/strong_proposer_protocol.md`; completed output `outputs/phase_strong_proposer_pilot_server.json`. | addressed for synthetic pilot |

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
| `outputs/toy_selection_failure.csv` | Local exact selection-failure toy table and false-certification metrics. |
| `outputs/toy_selection_failure_summary.json` | Local ACCS-v0 selected-rule diagnostics. |
| `outputs/toy_selection_failure_hardened.csv` | Local hardened baseline comparison. |
| `outputs/toy_selection_failure_sensitivity.csv` | Local ACCS-v0 sensitivity sweep over audit size, gamma, and delta. |
| `outputs/toy_policy_mismatch.csv` | Local policy-specific residual-cost toy. |
| `outputs/toy_no_overlap.csv` | Local no-overlap/support toy. |
| `outputs/toy_offpolicy_shift.csv` | Local off-policy query-shift toy: unweighted audit can fail under deployment Q, while known-ratio/support-capped rules expose the risk-yield/ESS cost. |
| `outputs/toy_offpolicy_shift_summary.md` | Readable summary for the off-policy query-shift toy. |
| `figures/figure1_selection_amplification.pdf` | Local Figure 1 prototype retained as a generated asset. |
| `figures/figure1_selection_amplification_hardened.pdf` | Hardened Figure 1 with strong local baselines; current main-paper version is redrawn in TikZ. |
| `aaai2027/tikz_figures.tex` | Current main-paper Figure 1 and Figure 2 source using LaTeX/TikZ/PGFPlots fonts. |
| `aaai2027/appendix.tex` | Current supplementary evidence package for experiments that do not fit the 7-page body. |
| `analysis/paper_assets/` | Local paper-ready figure/table package. |
| `analysis/local_results_summary.md` | Local result interpretation and supported/pending claims. |
| `analysis/strong_proposer_protocol.md` | Frozen query-bank and residual-label protocol for first strong-proposer pilot. |
| `outputs/phase_strong_proposer_pilot_server.json` | A40 synthetic OSRL-style fixed query-bank pilot with simulator-branch residual labels. |
| `outputs/phase_strong_proposer_pilot_server.md` | Compact report for the synthetic strong-proposer pilot. |
| `outputs/phase_strong_proposer_query_bank_server.npz` | Audit/test query-bank arrays for reproducing the pilot comparisons. |
| `analysis/paper_assets/table_strong_proposer_pilot_server.csv` | Compact table generated from the A40 synthetic strong-proposer pilot JSON. |
| `analysis/dsrl_caps_integration_status.md` | Negative DSRL/CAPS integration diagnostic and next-decision memo. |
| `src/run_dsrl_env_pilot.py` | DSRL simulator query-bank diagnostic script; not paper evidence yet. |
| `src/run_dsrl_dataset_pilot.py` | Official DSRL HDF5 logged-neighbor diagnostic script; not paper evidence yet. |
| `outputs/phase_dsrl_env_pilot_*.json` | Negative/inconclusive DSRL simulator diagnostics; preserve for debugging, do not promote to main claims. |
| `outputs/phase_dsrl_dataset_pilot_*.json` | Official DSRL HDF5 diagnostics; data path is solved but logged-neighbor proposer is not claim support. |
| `outputs/phase_dsrl_car_official_k64_q93_summary.md` | Three-seed official DSRL CarCircle bridge: selected-risk gap and selected-auditor controls. |
| `analysis/paper_assets/table_dsrl_car_official_k64_q93_seeds.csv` | Compact official DSRL bridge table. |
| `outputs/phase_dsrl_car_capsstyle_k64_q93_summary.md` | Three-seed official DSRL CarCircle CAPS-style bridge: candidate false below 5%, selected false above 5%. |
| `analysis/paper_assets/table_dsrl_car_capsstyle_k64_q93_seeds.csv` | Compact CAPS-style official DSRL bridge table. |
| `outputs/phase_dsrl_car_capsstyle_grid_summary.md` | Focused one-seed grid over q/risk/support bonuses for the CAPS-style official DSRL bridge. |
| `outputs/phase_dsrl_car_capsstyle_q92_risk025_support010_summary.md` | Five-seed high-signal CAPS-style official DSRL bridge: selected false about 10.4%, ACCS about 2.1%. |
| `analysis/paper_assets/table_dsrl_car_capsstyle_grid.csv` | Compact focused grid table. |
| `analysis/paper_assets/table_dsrl_car_capsstyle_q92_risk025_support010_seeds.csv` | Compact five-seed high-signal CAPS-style official DSRL bridge table. |
| `outputs/phase_dsrl_bc_heads_diagnostics_summary.md` | Trained weighted-BC multi-head proposer diagnostic; runs but currently weak selection gap. |
| `analysis/paper_assets/table_dsrl_bc_heads_diagnostics.csv` | Compact BC-heads diagnostic table. |
| `src/run_dsrl_capsiql_checkpoint_pilot.py` | Trained CAPSIQL checkpoint proposer evaluator on official DSRL HDF5. |
| `outputs/phase_dsrl_capsiql_checkpoint_50k_q93_summary.md` | Three-seed trained CAPSIQL checkpoint result: candidate false below 5%, top selected false above 5%. |
| `analysis/paper_assets/table_dsrl_capsiql_checkpoint_50k_q93_seeds.csv` | Compact trained CAPSIQL checkpoint three-seed table. |
| `scripts/summarize_capsiql_checkpoint_outputs.py` | Converts CAPSIQL checkpoint JSON outputs into compact CSV/Markdown tables. |
| `src/run_dsrl_cpq_checkpoint_pilot.py` | Trained CPQ checkpoint proposer evaluator on official DSRL HDF5. |
| `outputs/phase_dsrl_cpq_checkpoint_10k_q92_modelbest_summary.md` | CPQ 10k q0.92 model_best three-seed direct-baseline checkpoint result under the same auditor contract. |
| `outputs/phase_dsrl_cpq_checkpoint_10k_q93_modelbest_summary.md` | CPQ 10k q0.93 model_best three-seed conservative stability result. |
| `analysis/paper_assets/table_dsrl_cpq_checkpoint_10k_q92_modelbest_seeds.csv` | Compact CPQ 10k q0.92 model_best three-seed table. |
| `analysis/paper_assets/table_dsrl_cpq_checkpoint_10k_q93_modelbest_seeds.csv` | Compact CPQ 10k q0.93 model_best three-seed table. |
| `scripts/summarize_cpq_checkpoint_outputs.py` | Converts CPQ checkpoint JSON outputs into compact CSV/Markdown tables. |
| `src/run_dsrl_coptidice_checkpoint_pilot.py` | Trained COptiDICE checkpoint proposer evaluator on official DSRL HDF5. |
| `outputs/phase_dsrl_coptidice_checkpoint_10k_q92_modelbest_summary.md` | COptiDICE 10k q0.92 model_best three-seed direct-baseline checkpoint result. |
| `outputs/phase_dsrl_coptidice_checkpoint_10k_q93_modelbest_summary.md` | COptiDICE 10k q0.93 model_best three-seed stability result. |
| `analysis/paper_assets/table_dsrl_coptidice_checkpoint_10k_q92_modelbest_seeds.csv` | Compact COptiDICE 10k q0.92 model_best three-seed table. |
| `analysis/paper_assets/table_dsrl_coptidice_checkpoint_10k_q93_modelbest_seeds.csv` | Compact COptiDICE 10k q0.93 model_best three-seed table. |
| `scripts/summarize_coptidice_checkpoint_outputs.py` | Converts COptiDICE checkpoint JSON outputs into compact CSV/Markdown tables. |
| `analysis/main_table_protocol.md` | Frozen direct OSRL main-table protocol and reviewer-facing interpretation. |
| `analysis/paper_assets/table_main_direct_osrl.csv` | Consolidated CAPSIQL/CPQ/COptiDICE main-table asset with risk/yield tradeoffs. |
| `analysis/paper_assets/table_main_direct_osrl.md` | Human-readable main-table asset with percentage metrics. |
| `outputs/phase_dsrl_horizon_stress_summary.md` | CPQ/COptiDICE q0.92 H=20/H=80 residual-horizon stress summary. |
| `analysis/paper_assets/table_dsrl_horizon_stress.csv` | Compact residual-horizon stress table for CPQ and COptiDICE. |
| `src/run_dsrl_episode_proxy_audit.py` | Logged episode-block proxy auditor that groups issued query-block claims by anchor episode. |
| `outputs/phase_dsrl_episode_proxy_car_q92_summary.md` | CPQ/COptiDICE q0.92 logged episode-block proxy summary; scope-boundary evidence, not closed-loop guarantee. |
| `analysis/paper_assets/table_dsrl_episode_proxy_car_q92.csv` | Compact episode-proxy table for CPQ/COptiDICE q0.92. |
| `outputs/phase_dsrl_episode_cap1_proxy_car_q92_summary.md` | CPQ/COptiDICE q0.92 episode emission-budget proxy summary with cap=1. |
| `analysis/paper_assets/table_dsrl_episode_cap1_proxy_car_q92.csv` | Compact cap=1 emission-budget proxy table. |
| `outputs/phase_dsrl_episode_capsweep_proxy_car_q92_summary.md` | CPQ/COptiDICE q0.92 episode emission-budget sweep summary over caps 1/2/4/8. |
| `analysis/paper_assets/table_dsrl_episode_capsweep_proxy_car_q92.csv` | Compact emission-budget sweep table. |
| `analysis/paper_assets/table_dsrl_episode_capsweep_proxy_car_q92.tex` | Paper-ready LaTeX emission-budget sweep table inserted into `aaai2027/paper.tex`. |
| `analysis/closed_loop_audit_status.md` | Current true closed-loop simulator audit status and next experiment plan. |
| `src/run_dsrl_closed_loop_smoke.py` | Online DSRL rollout smoke for trained CPQ/COptiDICE checkpoints. |
| `src/run_dsrl_closed_loop_audit.py` | Online episode-budget diagnostic that fits threshold/cap rules on audit rollouts and evaluates on test rollouts. |
| `src/run_dsrl_closed_loop_fixed_cap_audit.py` | Pre-registered fixed-cap online episode audit with no score threshold fit on audit labels. |
| `scripts/run_closed_loop_frontier_4090.sh` | 4090 batch runner for fixed-cap closed-loop frontier jobs, with one GPU per job and tmux-safe logs. |
| `scripts/summarize_closed_loop_frontier_outputs.py` | Groups fixed-cap closed-loop JSON outputs by environment, proposer, and cap. |
| `outputs/phase_dsrl_closed_loop_fixed_cap_frontier_all_200x200_20260630_4090_summary.md` | Combined 4090 Car/Ball/Drone fixed-cap frontier summary over 3 seeds x 200 audit / 200 test episodes. |
| `analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_frontier_all_200x200_20260630_4090.csv` | Compact CSV for the earlier combined cap1/2/4/8 fixed-cap frontier; superseded by the full-cap asset for paper-facing claims. |
| `outputs/phase_dsrl_closed_loop_fixed_cap_frontier_caps64_200x200_20260630_4090_summary.md` | Intermediate 4090 Car/Ball/Drone fixed-cap frontier summary over caps 1/2/4/8/16/32/64. |
| `analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_frontier_caps64_200x200_20260630_4090.csv` | Intermediate compact CSV for the cap64 fixed-cap frontier. |
| `outputs/phase_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090_summary.md` | Current strongest 4090 Car/Ball/Drone fixed-cap saturation frontier over caps 64/128/256/512. |
| `analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090.csv` | Current paper-facing compact CSV for the full-cap fixed-cap frontier. |
| `src/run_dsrl_closed_loop_tuned_rule_audit.py` | Online tune/audit/test closed-loop rule diagnostic; tune selects a small rule family, audit/test evaluate the frozen selected rule. |
| `scripts/run_closed_loop_tuned_rule_4090.sh` | 4090 batch runner for the tune/audit/test closed-loop rule family. |
| `scripts/summarize_closed_loop_tuned_rule_outputs.py` | Aggregates selected frozen tuned-rule outputs across checkpoint seeds. |
| `outputs/phase_dsrl_closed_loop_tuned_rule_tuned_rule_100x200x200_20260630_4090_summary.md` | First completed 4090 tune/audit/test closed-loop diagnostic over Car/Ball/Drone, 3 seeds x 100 tune / 200 audit / 200 test. |
| `analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_tuned_rule_100x200x200_20260630_4090.csv` | Compact CSV for the first tuned-rule diagnostic; appendix candidate only unless a focused run meets the 5% target. |
| `outputs/tuned_rule_100x200x200_20260630_4090_logs/driver_status.tsv` | Tuned-rule 4090 driver trace; 18/18 jobs completed with 0 failures. |
| `outputs/phase_dsrl_closed_loop_tuned_rule_tuned_rule_drone_conservative_200x300x300_20260630_4090_summary.md` | Conservative Drone-only tuned-rule follow-up; too sparse to promote. |
| `analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_tuned_rule_drone_conservative_200x300x300_20260630_4090.csv` | Compact CSV for the conservative Drone-only tuned-rule follow-up. |
| `outputs/phase_dsrl_closed_loop_tuned_rule_tuned_rule_drone_medium_200x300x300_20260630_4090_summary.md` | Medium Drone-only tuned-rule follow-up; confirms threshold/cap-only tuning does not reach 5%. |
| `analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_tuned_rule_drone_medium_200x300x300_20260630_4090.csv` | Compact CSV for the medium Drone-only tuned-rule follow-up. |
| `outputs/frontier_200x200_20260630_4090_logs/driver_status.tsv` | Car/Ball 4090 fixed-cap frontier driver trace; 12/12 jobs completed. |
| `outputs/frontier_drone_200x200_20260630_4090_logs/driver_status.tsv` | Drone 4090 fixed-cap boundary driver trace; 6/6 jobs completed. |
| `outputs/phase_dsrl_closed_loop_fixed_cap_car_100x100_summary.md` | Historical three-seed CPQ/COptiDICE online 100/100 first-cap summary: CPQ test 5/300 with exact CP95 upper 3.47%; COptiDICE test 188/300 with exact CP95 upper 67.32%. |
| `analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_car_100x100_diagnostic.csv` | Compact CSV version of the pre-registered first-cap 100/100 closed-loop summary. |
| `outputs/phase_dsrl_closed_loop_fixed_cap_ball_matched_100x100_summary.md` | Matched BallCircle three-seed CPQ/COptiDICE online 100/100 first-cap summary: CPQ test 0/300 with exact CP95 upper 0.99%; COptiDICE test 256/300 with exact CP95 upper 88.59%. |
| `analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_ball_matched_100x100_diagnostic.csv` | Compact CSV version of the matched BallCircle pre-registered first-cap 100/100 closed-loop summary. |
| `analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_ball_matched_100x100.tex` | Compact LaTeX table for the BallCircle first-cap closed-loop result. |
| `outputs/phase_dsrl_closed_loop_fixed_cap_drone_matched_100x100_summary.md` | Matched DroneCircle three-seed CPQ/COptiDICE online 100/100 first-cap diagnostic: CPQ test 46/300 with exact CP95 upper 19.18%; COptiDICE test 294/300 with exact CP95 upper 99.13%. |
| `analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_drone_matched_100x100_diagnostic.csv` | Compact CSV version of the matched DroneCircle pre-registered first-cap 100/100 closed-loop diagnostic. |
| `analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_drone_matched_100x100.tex` | Compact LaTeX table for the DroneCircle boundary diagnostic. |
| `outputs/phase_dsrl_closed_loop_audit_cpq_car_100x100_summary.md` | Three-seed CPQ online 100/100 fixed-rule summary: 4/300 audit false episodes with exact CP95 upper 3.03%, and 7/300 test false episodes with exact CP95 upper 4.34%. |
| `outputs/phase_dsrl_closed_loop_audit_coptidice_car_100x100_summary.md` | Three-seed COptiDICE online 100/100 stress summary: mean test violation 61.67%, 131/231 test false issued episodes, and exact CP95 upper 62.20%. |
| `outputs/phase_dsrl_closed_loop_audit_car_30x30_summary.md` | Earlier three-seed online 30/30 diagnostic summary retained as a smoke trace. |
| `analysis/paper_assets/table_dsrl_closed_loop_audit_car_30x30_diagnostic.csv` | Compact CSV version of the closed-loop diagnostic summary. |
| `analysis/paper_assets/table_dsrl_closed_loop_audit_cpq_car_100x100_diagnostic.csv` | Compact CSV version of the CPQ 100/100 fixed-rule closed-loop audit summary. |
| `analysis/paper_assets/table_dsrl_closed_loop_audit_coptidice_car_100x100_diagnostic.csv` | Compact CSV version of the COptiDICE 100/100 closed-loop stress summary. |
| `outputs/phase_dsrl_closed_loop_audit_cpq_car_seed20260624_30x30_server.json` | CPQ CarCircle seed20260624 online 30/30 diagnostic; retained as per-seed trace. |
| `outputs/phase_dsrl_closed_loop_audit_coptidice_car_seed20260624_30x30_server.json` | COptiDICE CarCircle seed20260624 online 30/30 diagnostic; retained as per-seed trace. |
| `analysis/paper_assets/table_dsrl_ball_drone_10k_q92_feasibility.csv` | One-seed BallCircle/DroneCircle trained CPQ/COptiDICE q0.92 feasibility table. |
| `analysis/paper_assets/table_dsrl_ball_drone_10k_q92_feasibility.md` | Human-readable broader-environment feasibility summary. |
| `analysis/paper_assets/table_dsrl_coptidice_checkpoint_ball_10k_q92_modelbest_seeds.csv` | Three-seed COptiDICE BallCircle q0.92 robustness table. |
| `outputs/phase1_toy_moving_budget_server.json` | Server/canonical promotion target if needed. |
| `outputs/phase2_accs_prototype_server.json` | Expanded ACCS diagnostics. |
| `outputs/phase3_safety_gym_main_server.json` | Main benchmark table. |
| `outputs/phase4_caps_accs_server.json` | CAPS vs CAPS+ACCS evidence-layer comparison. |
| `outputs/phase5_shift_audit_server.json` | Distribution shift boundary. Superseded for local theory support by `outputs/toy_offpolicy_shift.csv`; server-scale shift audit remains optional. |
| `outputs/phase6_horizon_audit_server.json` | Horizon-level risk audit. |
| `analysis/paper_assets/table_main.csv` | Paper table generated from canonical outputs. |

---

## Current Verdict

The main claim stack is now supported at three levels. Exact toys and synthetic
pilots establish the selection-after-calibration failure mode; trained
CAPSIQL/CPQ/COptiDICE DSRL query-block audits establish the action-level
risk-yield story on official CarCircle; and the 4090 200/200 fixed-cap
closed-loop frontier establishes the strongest current episode-level audit
evidence. In the direct-OSRL main table, CPQ q0.92 has 7.17% top selected false
certification and ACCS-v0 reduces issued-claim risk to 2.25% at 80.18% yield;
COptiDICE q0.92 has 8.30% top false and ACCS-v0 gives 2.17% at 78.33% yield.
The logged episode proxy then shows why this action-level result is not a
trajectory guarantee: uncapped issued claims accumulate into 49.08% and 44.37%
episode-proxy false certification for CPQ and COptiDICE, respectively.

The current strongest closed-loop evidence is the 4090 fixed-cap frontier.
Under a pre-registered rule that issues certificates for the first `m` policy
steps with `m in {64,128,256,512}`, CPQ cap512 has 12/600 CarCircle test false
issued episodes with exact CP95 3.22% and 0/600 BallCircle test false issued
episodes with exact CP95 0.50%, while issuing full-episode certificates on both
environments. COptiDICE remains a matched unsafe stress contrast with 365/600
CarCircle and 533/600 BallCircle false issued test episodes. DroneCircle is a
boundary diagnostic rather than a third positive environment: CPQ has 90/600
test false issued episodes with exact CP95 17.61%, while COptiDICE has 576/600
with exact CP95 97.23%.

The tune/audit/test closed-loop rule diagnostics are useful but not a main
upgrade. The broad tuned run keeps CPQ Car/Ball positive and reduces CPQ
DroneCircle to 32/395 test false issued episodes with exact CP95 10.73%, but
this is still above the 5% target and selected rules vary across seeds. The
conservative Drone-only follow-up is too sparse (1/4, CP95 75.14%), and the
medium follow-up remains above target (54/581, CP95 11.52%). These results
support keeping DroneCircle as a harder-environment boundary diagnostic unless
a new method idea is introduced.

The AAAI draft now uses TikZ/PGFPlots figures, places Related Work before
Problem/Method, promotes the 4090 fixed-cap table in the main body, adds an
exact fixed-emission corollary for the closed-loop audit, and keeps the full cap
sweep in `aaai2027/appendix.tex`. The remaining evidence gaps are optional
higher-upside tuning/audit/test rules, SafeFQL comparator status, and final
claim-evidence consistency.
