# GPT Pro Prompt: Real-Proposer Experiment Redesign

Updated: 2026-06-24

Use this prompt when asking GPT Pro for a focused design review. Assume GPT Pro
has no memory of the project.

```text
You are advising a high-ambition ML/safe-RL paper project targeting an
oral-level AAAI/ICLR-style submission. Please read the following repository
files first and treat them as the project state:

1. idea_blueprint.md
2. experiment_report.md
3. NEXT_STEPS.md
4. analysis/strong_proposer_protocol.md
5. analysis/claim_evidence_map.md
6. analysis/dsrl_caps_integration_status.md
7. analysis/pro_review_2.md
8. src/run_strong_proposer_pilot.py
9. src/run_dsrl_env_pilot.py
10. src/run_dsrl_dataset_pilot.py
11. outputs/phase_strong_proposer_pilot_server.json
12. outputs/phase_dsrl_car_capsstyle_q92_risk025_support010_summary.md
13. outputs/phase_dsrl_capsiql_checkpoint_50k_q93_summary.md
14. outputs/phase_dsrl_cpq_checkpoint_10k_q92_modelbest_summary.md
15. outputs/phase_dsrl_cpq_checkpoint_10k_q93_modelbest_summary.md
16. src/run_dsrl_capsiql_checkpoint_pilot.py
17. src/run_dsrl_cpq_checkpoint_pilot.py
18. outputs/phase_dsrl_coptidice_checkpoint_10k_q92_modelbest_summary.md
19. outputs/phase_dsrl_coptidice_checkpoint_10k_q93_modelbest_summary.md
20. src/run_dsrl_coptidice_checkpoint_pilot.py
21. analysis/main_table_protocol.md
22. analysis/paper_assets/table_main_direct_osrl.md

Project thesis:
"Calibration before action selection is not calibration after action selection."
The paper targets false certification among issued action claims after
deployment-time action selection in offline safe RL.

What is already positive:
- Exact toys show selection amplification, continuation-policy mismatch, and
  no-overlap/support impossibility.
- The first A40 synthetic OSRL-style strong-proposer pilot succeeds:
  candidate false rate is about 3.24%, top-reward selected false rate is about
  15.99%, global candidate CP remains about 15.17%, and ACCS-v0 support+safety
  controls selected false certification to about 0.21% with full yield.
- The current best official-data bridge is DSRL CarCircle K64/q0.92 with a
  CAPS-style budget-head candidate generator over official HDF5 trajectories:
  across five seeds, candidate false certification is about 6.57%, top selected
  false certification is about 10.45%, global candidate CP controls only by
  collapsing to about 10.83% yield, CRC-style thresholding gets about 2.29% risk
  at 74.97% yield, and ACCS-v0 gets about 2.06% risk at 72.61% yield.
- A more conservative q0.93 CAPS-style bridge also exists: candidate false is
  about 4.09%, top selected false is about 6.84%, and ACCS-v0 is about 2.03%
  risk at 78.71% yield.
- The trained CAPSIQL 50k q0.93 route is now replicated across three seeds:
  candidate false is about 4.42%, top selected false is about 5.68%, CRC-style
  thresholding gets about 2.67% risk at 83.52% yield, and ACCS-v0 gets about
  2.28% risk at 80.60% yield.
- The direct CPQ 10k baseline is also replicated across three seeds under the
  same fixed query-bank/auditor contract. q0.93 model_best is conservative with
  top false about 4.60%; q0.92 model_best has top false about 7.17%, and
  ACCS-v0 controls selected false certification to about 2.25% at 80.18% yield.
- The direct COptiDICE 10k baseline is also replicated across three seeds. It is
  a stronger stress test than CPQ in this protocol: q0.93 model_best has top
  false about 5.86%, and q0.92 model_best has top false about 8.30%; ACCS-v0
  controls selected false certification to about 2.17-2.20% with 78-83% yield.

What is not solved:
- This synthetic pilot is not enough for a top-tier benchmark claim.
- Reward-bin/rank-bin/CRC-style baselines are serious and must remain in the
  paper.
- We now need to strengthen the frozen real-proposer main table with the most
  valuable next stress test or missing comparator so it can survive reviewer
  pressure from CAPS, SafeFQL, conformal risk control, and offline safe RL
  baselines.

Current bottleneck:
- The old data.offline-saferl.org endpoint is stale/unreachable, but current
  official DSRL HDF5 files were found on Hugging Face, downloaded locally, and
  copied to A40 under data/dsrl/.
- A project-local Python 3.10 environment can reset/step DSRL simulator tasks
  and load official BallCircle/CarCircle/DroneCircle HDF5 files.
- CAPS and OSRL source were cloned, but CAPS is a patch over OSRL/FSRL/torch
  and expects DSRL datasets/checkpoints; it is not a clean drop-in proposer.
- The self-generated DSRL query-bank script can produce cost events, but the
  selected-risk gap is unstable and the auditors become vacuous. Treat those
  outputs as negative diagnostics, not evidence.
- The official DSRL logged-neighbor query-bank script loads real HDF5 data. Its
  plain logged-neighbor smokes are diagnostic, but the CarCircle CAPS-style
  budget-head query-bank now gives a useful official-data bridge.
- The procedural CAPS-style bridge has been superseded as the main route by
  trained CAPSIQL, CPQ, and COptiDICE checkpoint evaluators. The first
  direct-OSRL main-table protocol is now frozen in
  `analysis/main_table_protocol.md` and
  `analysis/paper_assets/table_main_direct_osrl.md`. The most important
  experimental gap is no longer environment setup or main-table design; it is
  choosing the next stress test or missing comparator.
- A first trained weighted-BC multi-head proposer scaffold (`src/run_dsrl_bc_heads_pilot.py`)
  runs on A40 with torch 2.6 and direct HDF5 loading, but its current
  nearest-logged-action matching protocol is too conservative: top selected
  false remains close to candidate false. Treat it as a scaffold/negative
  diagnostic, not as the main route unless you propose a concrete upgrade.

Task:
Assume the current CAPSIQL/CPQ/COptiDICE direct-OSRL main-table protocol is
frozen. Design the strongest next experiment package that preserves the paper's
high ceiling. Do not recommend lowering the ambition or shrinking to a toy
paper. Give 2-3 concrete routes, ranked by expected reviewer credibility and
implementation time.

For each route, specify:
1. exact proposer source: real CAPS/OSRL checkpoint, trained OSRL policy,
   CAPS-style multi-head proposer, SafeFQL-style boundary, or another strong
   safe-RL policy;
2. how to obtain or generate the fixed query bank
   (s, B, {a_1,...,a_K}, reward_scores, cost_scores, support_scores);
3. how to define residual-cost labels without using an unrealistic oracle;
4. which baselines must be included beyond ACCS
   (global CP, reward-bin UCB, rank-bin UCB, CRC-style threshold, oracle, etc.);
5. the minimum result pattern that would be paper-worthy;
6. the likely reviewer attack and how to preempt it;
7. the first implementation step we should do in this repository.

Please be concrete enough that an engineer can implement the next script
without another strategy discussion.
```
