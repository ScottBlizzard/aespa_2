# src Code Map

This directory contains the local evidence package for AAAI_2.

## Implemented Local Modules

| File | Purpose |
|---|---|
| `eval_metrics.py` | Issued-claim metrics: selective risk, claim yield, reward, fallback rate. |
| `selective_auditor.py` | ACCS-v0 finite-rule selective auditor over threshold rules. |
| `toy_selection_failure.py` | Exact selection-amplification toy and Figure 1 prototype. |
| `toy_selection_failure_hardened.py` | Stronger local baselines and sensitivity sweep for the selection toy. |
| `toy_policy_mismatch.py` | Continuation-policy mismatch toy. |
| `toy_no_overlap.py` | No-overlap / unsupported-action indistinguishability toy. |
| `toy_offpolicy_shift.py` | Off-policy deployment-query shift toy with unweighted, weighted, and support-capped audits. |
| `run_strong_proposer_pilot.py` | Synthetic OSRL-style fixed query-bank pilot with simulator-branch residual labels. |
| `run_dsrl_env_pilot.py` | DSRL simulator query-bank diagnostic with learned reward/safety scorers. |
| `run_dsrl_dataset_pilot.py` | Official DSRL HDF5 logged-neighbor diagnostic with logged cost-to-go labels. |
| `run_dsrl_bc_heads_pilot.py` | Trained weighted-BC multi-head proposer diagnostic on official DSRL HDF5. |
| `run_dsrl_capsiql_checkpoint_pilot.py` | Trained CAPSIQL checkpoint proposer evaluator on official DSRL HDF5. |
| `run_dsrl_cpq_checkpoint_pilot.py` | Trained CPQ checkpoint proposer evaluator on official DSRL HDF5. |
| `run_dsrl_coptidice_checkpoint_pilot.py` | Trained COptiDICE checkpoint proposer evaluator on official DSRL HDF5. |

## Local Commands

Run from the repository root:

```powershell
python -m py_compile src\eval_metrics.py src\selective_auditor.py src\toy_selection_failure.py src\toy_policy_mismatch.py src\toy_no_overlap.py src\toy_offpolicy_shift.py src\run_strong_proposer_pilot.py src\run_dsrl_env_pilot.py src\run_dsrl_dataset_pilot.py src\run_dsrl_bc_heads_pilot.py src\run_dsrl_capsiql_checkpoint_pilot.py src\run_dsrl_cpq_checkpoint_pilot.py src\run_dsrl_coptidice_checkpoint_pilot.py
python src\toy_selection_failure.py
python src\toy_selection_failure_hardened.py
python src\toy_policy_mismatch.py
python src\toy_no_overlap.py
python src\toy_offpolicy_shift.py
python src\run_strong_proposer_pilot.py --no-query-bank
```

## Generated Outputs

```text
outputs/toy_selection_failure.csv
outputs/toy_selection_failure_summary.json
outputs/toy_selection_failure_hardened.csv
outputs/toy_selection_failure_hardened_summary.json
outputs/toy_selection_failure_sensitivity.csv
outputs/toy_policy_mismatch.csv
outputs/toy_no_overlap.csv
outputs/toy_offpolicy_shift.csv
outputs/toy_offpolicy_shift_summary.md
figures/figure1_selection_amplification.pdf
figures/figure1_selection_amplification_hardened.pdf
figures/figure1_sensitivity_hardened.pdf
figures/figure2_policy_mismatch.pdf
figures/figure3_no_overlap.pdf
figures/figure4_offpolicy_shift.pdf
outputs/phase_strong_proposer_pilot_server.json
outputs/phase_strong_proposer_pilot_server.md
outputs/phase_strong_proposer_query_bank_server.npz
outputs/phase_dsrl_env_pilot_*.json
outputs/phase_dsrl_env_pilot_*.md
outputs/phase_dsrl_dataset_pilot_*.json
outputs/phase_dsrl_dataset_pilot_*.md
outputs/phase_dsrl_capsiql_checkpoint_*.json
outputs/phase_dsrl_capsiql_checkpoint_*.md
outputs/phase_dsrl_cpq_checkpoint_*.json
outputs/phase_dsrl_cpq_checkpoint_*.md
outputs/phase_dsrl_coptidice_checkpoint_*.json
outputs/phase_dsrl_coptidice_checkpoint_*.md
```

## Server Command

On A40:

```bash
cd /workspace/thymic_project/paper/aaai_2
.venv/bin/python src/run_strong_proposer_pilot.py > outputs/log_phase_strong_proposer_pilot_server.txt 2>&1
```

DSRL simulator diagnostic on A40:

```bash
cd /workspace/thymic_project/paper/aaai_2
.venv310/bin/python src/run_dsrl_env_pilot.py \
  > outputs/log_phase_dsrl_env_pilot_server.txt 2>&1
```

The DSRL script is currently diagnostic-only. It documents the real-proposer
integration bottleneck and should not be used as paper-facing evidence until the
query law and proposer are redesigned or connected to real DSRL data/checkpoints.

Official DSRL HDF5 diagnostic on A40:

```bash
cd /workspace/thymic_project/paper/aaai_2
.venv310/bin/python src/run_dsrl_dataset_pilot.py --env-id OfflineCarCircle-v0 \
  > outputs/log_phase_dsrl_dataset_pilot_car_server.txt 2>&1
```

This script verifies the official DSRL data path and logged residual-label
machinery. The first logged-neighbor smoke runs do not show the desired
selection amplification, so they are diagnostics rather than paper evidence.

Trained BC-head proposer diagnostic on A40:

```bash
cd /workspace/thymic_project/paper/aaai_2
.venv/bin/python src/run_dsrl_bc_heads_pilot.py --env-id OfflineCarCircle-v0 \
  --risk-quantile 0.92 --no-query-bank
```

This script uses torch 2.6 in `.venv` and loads HDF5 directly, avoiding the
Python 3.10 no-torch environment. The current nearest-logged-action matching
version runs but is not a main result because it does not create a strong
selection-amplification gap.

Current best official DSRL bridge:

```text
outputs/phase_dsrl_car_capsstyle_q92_risk025_support010_summary.md
analysis/paper_assets/table_dsrl_car_capsstyle_q92_risk025_support010_seeds.csv
```

Current trained CAPSIQL checkpoint result:

```text
outputs/phase_dsrl_capsiql_checkpoint_50k_q93_summary.md
analysis/paper_assets/table_dsrl_capsiql_checkpoint_50k_q93_seeds.csv
```

Current trained CPQ direct-baseline result:

```text
outputs/phase_dsrl_cpq_checkpoint_10k_q92_modelbest_summary.md
analysis/paper_assets/table_dsrl_cpq_checkpoint_10k_q92_modelbest_seeds.csv
outputs/phase_dsrl_cpq_checkpoint_10k_q93_modelbest_summary.md
analysis/paper_assets/table_dsrl_cpq_checkpoint_10k_q93_modelbest_seeds.csv
```

Current trained COptiDICE direct-baseline result:

```text
outputs/phase_dsrl_coptidice_checkpoint_10k_q92_modelbest_summary.md
analysis/paper_assets/table_dsrl_coptidice_checkpoint_10k_q92_modelbest_seeds.csv
outputs/phase_dsrl_coptidice_checkpoint_10k_q93_modelbest_summary.md
analysis/paper_assets/table_dsrl_coptidice_checkpoint_10k_q93_modelbest_seeds.csv
```

Canonical evaluator command shape:

```bash
cd /workspace/thymic_project/paper/aaai_2
PYTHONPATH=/workspace/thymic_project/paper/aaai_2/external/OSRL \
.venv/bin/python src/run_dsrl_capsiql_checkpoint_pilot.py \
  --checkpoint outputs/capsiql_car_logs_50k_5/OfflineCarCircle-v0/<run>/<run>/checkpoint/model.pt \
  --risk-quantile 0.93 \
  --reward-risk-bonus 0.00 \
  --model-reward-weight 1.00 \
  --model-cost-weight 0.00 \
  --no-query-bank
```

Canonical CPQ evaluator command shape:

```bash
cd /workspace/thymic_project/paper/aaai_2
PYTHONPATH=/workspace/thymic_project/paper/aaai_2/external/OSRL \
.venv/bin/python src/run_dsrl_cpq_checkpoint_pilot.py \
  --checkpoint outputs/cpq_car_logs_10k/OfflineCarCircle-v0/<run>/<run>/checkpoint/model_best.pt \
  --risk-quantile 0.92 \
  --proposal-samples 96 \
  --no-query-bank
```

Canonical COptiDICE evaluator command shape:

```bash
cd /workspace/thymic_project/paper/aaai_2
PYTHONPATH=/workspace/thymic_project/paper/aaai_2/external/OSRL \
.venv/bin/python src/run_dsrl_coptidice_checkpoint_pilot.py \
  --checkpoint outputs/coptidice_car_logs_10k/OfflineCarCircle-v0/<run>/<run>/checkpoint/model_best.pt \
  --risk-quantile 0.92 \
  --proposal-samples 96 \
  --no-query-bank
```

## Planned Server / Benchmark Modules

| File | Purpose |
|---|---|
| `proposal_stream.py` | Frozen query-bank interface for real safe-RL proposers. |
| `conformal.py` | Reusable global/group/rank conformal primitives. |
| `risk_control.py` | CRC/CAP/FCR-style baselines. |
| `support.py` | Support diagnostics and off-policy effective-sample-size checks. |
| `run_caps_pilot.py` | First CAPS integration. |
| `run_safefql_pilot.py` | First SafeFQL integration if feasible. |
| `plot_paper_figures.py` | Rebuild paper-ready figures from canonical outputs. |

The synthetic strong-proposer pilot is complete. The first trained CAPSIQL
checkpoint pilot is complete on CarCircle q0.93 across three 50k seeds. CPQ and
COptiDICE now both have 10k direct-baseline checkpoint results across three
seeds under the same auditor contract. Next server work should preserve the
same query-bank/report contract while deciding the main table and adding
SafeFQL only if it can be made comparable.
