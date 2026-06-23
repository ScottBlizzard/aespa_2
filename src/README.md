# src Code Plan

This directory will contain the ACCS implementation and experiment runners.

## Planned Modules

| File | Purpose |
|---|---|
| `config.py` | Common paths, seeds, budgets, alpha values, environment config. |
| `data_io.py` | JSON/JSONL/CSV helpers. |
| `toy_env.py` | Moving-budget toy safe RL environment. |
| `offline_data.py` | Offline trajectory generation and train/calibration/test splits. |
| `cost_model.py` | Cost-return predictor and ensemble utilities. |
| `action_groups.py` | Action/risk group construction. |
| `conformal.py` | Nonconformity scores, conformal quantiles, hierarchical fallback. |
| `shield.py` | ACCS execute/replace/abstain logic. |
| `eval_metrics.py` | Utility, calibration, adaptivity, horizon metrics. |
| `baselines.py` | No shield, global conformal, state-only, pessimism baselines. |
| `run_phase1_toy.py` | Toy moving-budget main phenomenon. |
| `run_phase2_accs.py` | ACCS prototype and diagnostics. |
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

