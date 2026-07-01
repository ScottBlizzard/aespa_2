# Ball/Drone 10k q0.92 Feasibility

Single-seed trained CPQ/COptiDICE checkpoint audit on official DSRL BallCircle
and DroneCircle, seed 20260624. Values are percentages except reward.

| proposer | env | candidate F | top F | global R/Y | reward-bin R/Y | CRC R/Y | ACCS R/Y | read |
|---|---|---:|---:|---:|---:|---:|---:|---|
| CPQ | BallCircle | 6.35 | 5.95 | 1.72 / 82.56 | 1.11 / 49.51 | 2.52 / 90.23 | 1.88 / 85.94 | useful stability, not selection-amplification |
| CPQ | DroneCircle | 2.35 | 3.04 | 3.01 / 99.83 | 2.82 / 95.88 | 2.93 / 99.97 | 2.12 / 88.71 | low-risk robustness supplement |
| COptiDICE | BallCircle | 6.15 | 6.53 | 5.33 / 96.12 | 5.27 / 60.37 | 3.57 / 87.64 | 2.94 / 80.46 | strongest broader-env candidate |
| COptiDICE | DroneCircle | 2.27 | 3.19 | 3.21 / 100.00 | 2.98 / 100.00 | 3.21 / 100.00 | 2.84 / 98.18 | low-risk robustness supplement |

Single-seed interpretation:

BallCircle, especially COptiDICE BallCircle, is the only one-seed broader-env
result that looks worth expanding immediately. It gives a nontrivial selected
false rate, global/reward-bin baselines that are close to or above the target,
and an ACCS-v0 rule below 5% with about 80% yield. DroneCircle is useful as a
robustness check that the auditor does not collapse outside CarCircle, but its
low base risk makes it weaker as a headline stress test.

Three-seed follow-up:

The COptiDICE BallCircle expansion was run for seeds 20260624/20260625/20260626.
The mean top false rate drops to 4.85% and the mean selection gap is -0.29%,
while ACCS-v0 remains useful at 2.48% risk and 88.61% yield. This makes
BallCircle a robustness/stability result, not a stronger headline stress row
than CarCircle. The three-seed summary is
`outputs/phase_dsrl_coptidice_checkpoint_ball_10k_q92_modelbest_summary.md`;
the CSV is
`analysis/paper_assets/table_dsrl_coptidice_checkpoint_ball_10k_q92_modelbest_seeds.csv`.
