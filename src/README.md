# src Code Plan

This directory will contain the selection-aware calibration implementation and experiment runners.

## Planned Modules

| File | Purpose |
|---|---|
| `config.py` | Common paths, seeds, budgets, alpha values, environment config. |
| `data_io.py` | JSON/JSONL/CSV helpers. |
| `toy_selection_failure.py` | Exact finite MDP / one-state K-action counterexample. |
| `offline_data.py` | Offline trajectory generation and train/calibration/test splits. |
| `cost_model.py` | Cost-return predictor and ensemble utilities. |
| `proposal_stream.py` | Fixed proposal/query-bank interface and candidate-set construction. |
| `continuation.py` | Declared continuation policy and fallback policy interfaces. |
| `conformal.py` | Global and group split-conformal primitives. |
| `risk_control.py` | Conformal risk control and selective/FCR baseline hooks. |
| `selection.py` | Highest-reward certified action and alternative selection rules. |
| `support.py` | Support diagnostics and no-overlap abstention. |
| `eval_metrics.py` | False certification, claim yield, risk-coverage, utility, fallback cost, horizon metrics. |
| `baselines.py` | Uncalibrated score, global CP, group CP, CRC/selective baselines. |
| `run_phase1_toy.py` | Exact selection-failure toy phenomenon. |
| `run_phase2_accs.py` | Selection-aware ACCS prototype and diagnostics. |
| `run_phase3_safety_gym.py` | Safety-Gymnasium benchmark. |
| `run_phase4_dsrl.py` | DSRL benchmark. |
| `plot_paper_figures.py` | Generate tables/figures from canonical outputs. |

## Output Rule

Experiment runners should write machine-readable JSON and optional Markdown summaries:

```text
../outputs/<phase>_<name>_server.json
../outputs/<phase>_<name>_server.md
```

Local smoke tests should include `local_smoke` in the filename and must not be used as paper evidence.
