# Main Direct OSRL Table

> Updated: 2026-06-24
> Source CSV: `analysis/paper_assets/table_main_direct_osrl.csv`

All rows use official DSRL `OfflineCarCircle-v0`, three seeds
`20260624/20260625/20260626`, the same fixed query-bank/auditor contract, and
fractional metrics converted to percentages below.

| Role | Proposer | q | Candidate false | Top selected false | Global CP risk/yield | Reward-bin risk/yield | CRC risk/yield | ACCS risk/yield |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| mainline | CAPSIQL 50k | 0.93 | 4.42 +/- 0.43 | 5.68 +/- 0.25 | 0.09 / 3.81 | 3.59 / 71.71 | 2.67 / 83.52 | 2.28 / 80.60 |
| main high-signal | CPQ 10k | 0.92 | 6.40 +/- 0.68 | 7.17 +/- 0.67 | 0.08 / 7.33 | 1.99 / 60.96 | 2.78 / 83.44 | 2.25 / 80.18 |
| main stress | COptiDICE 10k | 0.92 | 6.36 +/- 0.57 | 8.30 +/- 0.76 | 0.13 / 8.08 | 3.12 / 57.94 | 2.28 / 79.15 | 2.17 / 78.33 |
| stability | CPQ 10k | 0.93 | 4.13 +/- 0.49 | 4.60 +/- 0.51 | 0.05 / 7.33 | 1.88 / 73.48 | 2.82 / 91.97 | 2.42 / 89.49 |
| stability | COptiDICE 10k | 0.93 | 4.16 +/- 0.45 | 5.86 +/- 0.29 | 0.03 / 8.08 | 3.10 / 70.88 | 2.69 / 86.07 | 2.20 / 83.12 |

Interpretation:

```text
Global CP has low risk but low yield, so it is not the practical comparator.
Reward-bin and CRC-style auditors are strong baselines. ACCS-v0 should be
presented as a support-aware certification rule that keeps selected-claim risk
near 2.2-2.3% while retaining about 78-81% yield in the high-signal rows.
```
