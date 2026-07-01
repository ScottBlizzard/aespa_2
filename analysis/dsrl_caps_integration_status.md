# DSRL / CAPS Integration Status

Updated: 2026-06-23

## Summary

The first synthetic strong-proposer pilot succeeded. The DSRL data-access issue
has now been resolved by using the current official Hugging Face dataset mirror
from the DSRL GitHub repository.

Current verdict:

```text
The trained CAPSIQL route is now working end-to-end on A40. The previous
CAPS-style K64/q0.92/q0.93 bridges remain useful, but the current mainline is
now a real CAPSIQL checkpoint proposer on official DSRL CarCircle HDF5 data.
```

## What Worked

### Project-local Python 3.10 environment

A second project-local environment was created on A40:

```text
/workspace/thymic_project/paper/aaai_2/.venv310
```

Reason:

```text
safety-gymnasium 0.4.0 / DSRL imports cleanly under Python 3.10.
The Python 3.11 .venv hits safety-gymnasium dataclass mutable-default errors.
```

Installed in `.venv310`:

```text
dsrl==0.1.0
safety-gymnasium==0.4.0
gymnasium==0.28.1
gym==0.26.2
numpy==1.26.4
h5py
pandas
matplotlib
scikit-learn
scipy
tqdm
```

### DSRL environment reset/step

These DSRL simulator tasks reset and step successfully:

```text
OfflineCarCircle-v0
OfflineAntRun-v0
OfflineBallCircle-v0
OfflineDroneCircle-v0
```

`OfflineBallCircle-v0` produced the clearest cost signal under random rollouts.

### CAPS and OSRL source code

Both repositories were cloned inside the project:

```text
external/CAPS
external/OSRL
```

CAPS is not standalone. It is a patch over OSRL and expects:

```text
OSRL package layout
FSRL logger utilities
pyrallis
torch
DSRL datasets
```

The key CAPS action-selection logic is in:

```text
external/CAPS/osrl/algorthims/capsiql.py::CapsIQLTrainer.select_head_q
external/CAPS/osrl/algorthims/capssac.py::CapsSACTrainer.select_head
```

CAPS was integrated into the project-local OSRL copy on A40, and `CapsIQL` /
`CapsIQLTrainer` now import under:

```text
/workspace/thymic_project/paper/aaai_2/.venv
PYTHONPATH=/workspace/thymic_project/paper/aaai_2/external/OSRL
```

The Python 3.11 `.venv` was patched locally for Safety-Gymnasium dataclass
defaults and supplemented with the lightweight OSRL/CAPS dependencies needed
for CAPSIQL training. This does not modify other project folders.

### Official DSRL HDF5 data

The old PyPI `dsrl==0.1.0` package points to a stale endpoint:

```text
http://data.offline-saferl.org/download/SafetyCarCircle-v0-100-1450.hdf5
```

That host resolves but does not accept TCP connections from local Windows, and
times out from A40. The current DSRL GitHub repository uses Hugging Face URLs
instead, for example:

```text
https://huggingface.co/datasets/YYY-45/DSRL/resolve/main/SafetyCarCircle-v0-100-1450.hdf5
https://huggingface.co/datasets/YYY-45/DSRL/resolve/main/SafetyBallCircle-v0-80-886.hdf5
https://huggingface.co/datasets/YYY-45/DSRL/resolve/main/SafetyDroneCircle-v0-100-1923.hdf5
```

Local Windows can access those URLs. A40 currently cannot reach the
`huggingface.co` entry host directly, so the files were downloaded locally and
copied into:

```text
/workspace/thymic_project/paper/aaai_2/data/dsrl/
```

Validated on A40 with `DSRL_DATASET_DIR=/workspace/thymic_project/paper/aaai_2/data/dsrl`:

| Env | File | Shape |
|---|---|---|
| `OfflineBallCircle-v0` | `SafetyBallCircle-v0-80-886.hdf5` | observations `(177200, 8)`, actions `(177200, 2)` |
| `OfflineCarCircle-v0` | `SafetyCarCircle-v0-100-1450.hdf5` | observations `(435000, 8)`, actions `(435000, 2)` |
| `OfflineDroneCircle-v0` | `SafetyDroneCircle-v0-100-1923.hdf5` | observations `(576243, 18)`, actions `(576243, 4)` |

## What Still Failed

### Earlier Python 3.11 Safety-Gymnasium issue

The original project `.venv` had torch, but `safety_gymnasium` initially failed:

```text
ValueError: mutable default <class 'numpy.ndarray'> for field color is not allowed: use default_factory
```

This was a Python 3.11 compatibility issue in the installed Safety-Gymnasium
package, not in AAAI_2 code. It has been fixed inside the project-local A40
`.venv`; `.venv310` remains useful for older DSRL simulator diagnostics.

### Self-generated DSRL query bank

Implemented:

```text
src/run_dsrl_env_pilot.py
```

The script can:

- create DSRL simulator query states;
- replay prefix trajectories;
- generate candidate actions;
- fit lightweight learned reward/residual-cost scorers;
- run the same global/reward-bin/rank-bin/CRC/ACCS auditor matrix;
- emit server JSON/MD reports.

But the current results are not a usable positive result.

Representative diagnostics:

| Run | Setting | Outcome |
|---|---|---|
| `phase_dsrl_env_pilot_smoke_ball_h50` | reset states, H=50, q=0.90 | candidate false 0.1023, selected false 0.1188, all auditors 0 yield |
| `phase_dsrl_env_pilot_medium` | reset states, H=50, q=0.90 | candidate false 0.1016, selected false 0.1100, all auditors 0 yield |
| `phase_dsrl_env_pilot_medium_alpha10` | reset states, alpha=0.10 | selected false 0.1063, all auditors 0 yield |
| `phase_dsrl_env_pilot_prefix_smoke` | prefix states, H=20, q=0.90 | candidate false 0.1159, selected false 0.1400, all auditors 0 yield |
| `phase_dsrl_env_pilot_medium_prefix` | prefix states, H=20, q=0.90 | audit selected false 0.1250, test selected false 0.0863, all auditors 0 yield |
| `phase_dsrl_env_pilot_prefix_q95` | prefix states, H=20, q=0.95 | no failures on audit/test |

Interpretation:

```text
The current self-generated DSRL setup can create cost events, but the
selection-induced gap is unstable and the learned safety score does not support
non-vacuous certification under the current auditor matrix.
```

### Official dataset logged-neighbor query bank

Implemented:

```text
src/run_dsrl_dataset_pilot.py
```

This script uses official DSRL HDF5 trajectories, constructs candidate banks
from nearest logged states, and labels candidates by logged future cost-to-go.
It is real data, but not yet a strong CAPS/OSRL proposer.

Representative diagnostics:

| Run | Setting | Outcome |
|---|---|---|
| `phase_dsrl_dataset_pilot_ball_smoke` | BallCircle, alpha 0.05 | candidate false 0.1015, top false 0.0940, auditors vacuous |
| `phase_dsrl_dataset_pilot_car_smoke` | CarCircle, alpha 0.05 | candidate false 0.0802, top false 0.0712, global CP risk 0.0366 at yield 0.9064 |
| `phase_dsrl_dataset_pilot_drone_smoke` | DroneCircle, alpha 0.05 | candidate false 0.0209, top false 0.0216, no meaningful selection gap |
| `phase_dsrl_dataset_pilot_ball_alpha10` | BallCircle, alpha 0.10 | candidate false 0.1039, top false 0.0988, reward-bin low yield |
| `phase_dsrl_car_official_k64_q93_summary` | CarCircle, K=64, q=0.93, 3 seeds | candidate false 0.0542, top false 0.0678; global CP risk 0.0578/yield 0.9626; ACCS risk 0.0193/yield 0.7024 |
| `phase_dsrl_car_capsstyle_k64_q93_summary` | CarCircle, K=64, q=0.93, CAPS-style budget heads, 3 seeds | candidate false 0.0409, top false 0.0684; ACCS risk 0.0203/yield 0.7871 |
| `phase_dsrl_car_capsstyle_q92_risk025_support010_summary` | CarCircle, K=64, q=0.92, CAPS-style budget heads, 5 seeds | candidate false 0.0657, top false 0.1045; global CP risk 0.0010/yield 0.1083; CRC risk 0.0229/yield 0.7497; ACCS risk 0.0206/yield 0.7261 |
| `phase_dsrl_bc_heads_diagnostics_summary` | CarCircle, trained weighted-BC multi-head proposer, q=0.92 | runs on torch 2.6/HDF5 path, but selection gap is weak: top false 0.0736-0.0790 vs candidate false about 0.0748 |
| `phase_dsrl_capsiql_checkpoint_50k_q93_summary` | CarCircle, trained CAPSIQL 50k checkpoint, q=0.93, 3 seeds | clean trained-checkpoint result: candidate false 0.0442, top false 0.0568, CRC risk 0.0267/yield 0.8352, ACCS risk 0.0228/yield 0.8060 |
| `phase_dsrl_cpq_checkpoint_10k_q92_modelbest_summary` | CarCircle, trained CPQ 10k checkpoint, q=0.92, 3 seeds | direct OSRL baseline: candidate false 0.0640, top false 0.0717, CRC risk 0.0278/yield 0.8344, ACCS risk 0.0225/yield 0.8018 |
| `phase_dsrl_cpq_checkpoint_10k_q93_modelbest_summary` | CarCircle, trained CPQ 10k checkpoint, q=0.93, 3 seeds | conservative stability check: candidate false 0.0413, top false 0.0460, CRC risk 0.0282/yield 0.9197, ACCS risk 0.0242/yield 0.8949 |
| `phase_dsrl_coptidice_checkpoint_10k_q92_modelbest_summary` | CarCircle, trained COptiDICE 10k checkpoint, q=0.92, 3 seeds | direct OSRL baseline: candidate false 0.0636, top false 0.0830, CRC risk 0.0228/yield 0.7915, ACCS risk 0.0217/yield 0.7833 |
| `phase_dsrl_coptidice_checkpoint_10k_q93_modelbest_summary` | CarCircle, trained COptiDICE 10k checkpoint, q=0.93, 3 seeds | conservative stability check: candidate false 0.0416, top false 0.0586, CRC risk 0.0269/yield 0.8607, ACCS risk 0.0220/yield 0.8312 |
| `table_dsrl_ball_drone_10k_q92_feasibility` | BallCircle/DroneCircle, trained CPQ/COptiDICE 10k checkpoints, q=0.92, seed 20260624 | broader-env one-seed feasibility: COptiDICE BallCircle looked strongest with top false 0.0653 and ACCS 0.0294/yield 0.8046; DroneCircle is lower-risk robustness evidence |
| `phase_dsrl_coptidice_checkpoint_ball_10k_q92_modelbest_summary` | BallCircle, trained COptiDICE 10k checkpoint, q=0.92, 3 seeds | three-seed follow-up: candidate false 0.0515, top false 0.0485, CRC 0.0282/yield 0.9173, ACCS 0.0248/yield 0.8861; robustness evidence, not headline stress |
| `phase_dsrl_episode_proxy_car_q92_summary` | CarCircle, trained CPQ/COptiDICE 10k checkpoints, q=0.92, 3 seeds | logged episode-block proxy: CPQ ACCS block risk 0.0225/yield 0.8018 but episode-proxy false 0.4908; COptiDICE ACCS block risk 0.0217/yield 0.7833 but episode-proxy false 0.4437; boundary evidence, not closed-loop guarantee |
| `phase_dsrl_episode_cap1_proxy_car_q92_summary` | CarCircle, trained CPQ/COptiDICE 10k checkpoints, q=0.92, 3 seeds | sparse emission-budget proxy: ACCS+cap1 reduces episode-proxy false to 0.0046 on CPQ and 0.0069 on COptiDICE with 100% episode yield, but only 2.42% block yield |
| `phase_dsrl_episode_capsweep_proxy_car_q92_summary` | CarCircle, trained CPQ/COptiDICE 10k checkpoints, q=0.92, 3 seeds | emission-budget sweep over caps 1/2/4/8: ACCS+cap4 keeps episode-proxy false at 0.0253 on CPQ and 0.0264 on COptiDICE with 9.67% block yield; cap8 rises above the 5% target |

Interpretation:

```text
The official HDF5 data path is fixed. Ball/Drone logged-neighbor proposers were
too weak, but CarCircle K64 gives useful selected-risk bridges. The q0.92
CAPS-style bridge is still the strongest procedural bridge: selected false
certification rises to about 10.4% across five seeds while ACCS-v0 reduces it
to about 2.1% with about 72.6% yield.

The trained-proposer credibility gap is now partially closed. Across three
50k-step CAPSIQL checkpoint seeds, q0.93 gives a clean
selection-amplification result: candidate false certification is below 5%,
while top selected false certification exceeds 5%. ACCS-v0 controls selected
false certification to about 2.3% with about 80.6% yield.

The direct OSRL baselines are now also replicated. CPQ 10k q0.92 model_best is
higher-signal than q0.93, with about 7.2% top-selected false certification,
while ACCS-v0 controls selected false certification to about 2.3% at about
80.2% yield. COptiDICE 10k is an even stronger stress test in this protocol:
q0.92 has about 8.3% top-selected false certification, and q0.93 still has
about 5.9%; ACCS-v0 controls selected false certification to about 2.2% with
78-83% yield. The direct-OSRL main table is now frozen in
`analysis/main_table_protocol.md`.

The first residual-horizon stress test is also complete for CPQ/COptiDICE
q0.92 at H=20 and H=80. At H=20, ACCS-v0 keeps selected false certification at
about 2.1-2.3% with about 93-95% yield. At H=80, ACCS-v0 remains below 5%
with about 80-85% yield, but global/reward-bin/CRC baselines become much closer
competitors. The remaining need is external SafeFQL comparison, broader
environment stress, or a true closed-loop episode audit, not environment setup.

The first trained broader-environment feasibility pass is now complete. The
one-seed COptiDICE BallCircle row looked like a possible expansion target, but
the three-seed follow-up is more conservative: top selected false certification
averages about 4.85% and the mean selection gap is negative. ACCS-v0 still gives
2.48% risk at 88.61% yield, so the result is useful as robustness/stability
evidence rather than as a stronger headline stress row than CarCircle. DroneCircle
is also lower-risk robustness evidence.

The first logged episode-block proxy is also complete. It uses the same frozen
CPQ/COptiDICE q0.92 query blocks and groups issued claims by their logged anchor
episode. This is deliberately not presented as closed-loop simulator evidence:
it shows that a 2.2% block-level selected false-certification rate can still
accumulate to 44-49% episode-proxy false certification when roughly 32-33
claims are issued per episode. This strengthens the next research target:
explicit risk allocation or true closed-loop episode auditing.

The emission-budget sweep is the first positive result in that direction. It
caps each logged episode to 1/2/4/8 issued certificates after applying the same
auditor masks. Under this sparse certificate regime, ACCS-v0+cap1 has 0.46%
episode-proxy false certification on CPQ and 0.69% on COptiDICE, with 100%
episode yield but 2.42% block yield. ACCS-v0+cap4 raises block yield to 9.67%
while keeping episode-proxy false certification at 2.53%/2.64%; cap8 starts to
exceed the 5% target. This is not the final trajectory method, but it shows
that the risk-allocation branch is technically live.

SafeFQL remains the most important external comparator, but it is not currently
runnable from public code in this workspace. On 2026-06-24, the paper page
linked to `https://tau-intelligence.com/safe-fql/` and
`https://github.com/tau-intelligence/safe-fql`; `git ls-remote` resolved the
repository to main commit `5774862564432bbfcfd16d511c986001978108e5`, but the
public repository only exposes a README/placeholder-style state with no
training, checkpoint, or evaluator code.
```

## Why This Is Still A Real Bottleneck

The blocker is not syntax, data access, or environment setup anymore. It is the
experiment object:

1. Self-generated DSRL query banks do not yet yield a stable selected-risk gap
   with useful non-vacuous auditors.
2. Official DSRL CAPS-style CarCircle K64/q93 yields a useful bridge but is not
   a trained-policy baseline.
3. The first trained CAPSIQL checkpoint result is replicated over three seeds.
4. CPQ and COptiDICE direct baselines are completed across three seeds.
5. The first consolidated direct-OSRL main table is frozen.
6. The first CPQ/COptiDICE residual-horizon stress test is completed at H=20
   and H=80 over three seeds each.
7. BallCircle/DroneCircle trained checkpoint feasibility is completed for
   CPQ/COptiDICE at seed 20260624, and COptiDICE BallCircle q0.92 has been
   expanded to three seeds as robustness evidence.
8. The logged episode-block proxy is completed for CPQ/COptiDICE q0.92 and
   identifies the action-certificate versus episode-safety boundary.
9. The episode emission-budget sweep over caps 1/2/4/8 is completed and gives
   a positive sparse risk-allocation diagnostic.
10. SafeFQL is now documented as critical prior work, but its current public
   repository is not an immediately runnable comparator.

## Recommended Next Decision

Next choices:

1. **Promote trained CAPSIQL checkpoint pilots to the current mainline.**
   Keep the CAPS-style bridge as a procedural reference, not the headline.

2. **Use the frozen direct-baseline main table as the CarCircle core.**
   CAPSIQL, CPQ, and COptiDICE now share the same query-bank/residual-label
   auditor contract. The consolidated asset is
   `analysis/paper_assets/table_main_direct_osrl.md`.

3. **Keep BallCircle/DroneCircle as robustness evidence.**
   COptiDICE BallCircle q0.92 is now three-seed and does not beat the CarCircle
   stress story: top false is 0.0485 and ACCS is 0.0248/yield 0.8861. Do not
   spend more GPU on this branch unless an appendix robustness table is needed.

4. **Use the residual-horizon stress as the moving-budget evidence.**
   The completed asset is
   `outputs/phase_dsrl_horizon_stress_summary.md`; write it as residual-label
   stress, not closed-loop episode safety.

5. **Use the episode-block proxy to motivate the next upper-bound audit.**
   The completed asset is
   `outputs/phase_dsrl_episode_proxy_car_q92_summary.md`, with cap=1 follow-up
   in `outputs/phase_dsrl_episode_cap1_proxy_car_q92_summary.md` and full cap
   sweep in `outputs/phase_dsrl_episode_capsweep_proxy_car_q92_summary.md`. It
   should motivate a tunable emission budget or a true closed-loop simulator
   audit, not replace the action-level selected-risk main table.

6. **Use the official dataset pilot as the data contract.**
   Keep `run_dsrl_dataset_pilot.py` for data loading and logged residual labels,
   but replace the logged-neighbor proposer with a stronger proposer.

Core question for pro:

```text
Given the frozen CAPSIQL/CPQ/COptiDICE direct-OSRL main-table protocol, what is
the most valuable next stress test or missing comparator for an oral-level
submission: SafeFQL, broader DSRL environments, horizon-level episode audit, or
a stronger theory/ablation package?
```
