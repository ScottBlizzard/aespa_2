# Local Results Summary

Updated: 2026-06-23

This note summarizes the local evidence package. It is not a server benchmark report.

---

## 1. Exact Selection-Amplification Toy

Construction:

```text
X_j ~ Uniform[0,1]
R_j = X_j
Z_j = 1{X_j > 0.96}
B = 0.5
per-action false rate = 4%
```

A global/marginal certifier issues all candidate actions. The deployment rule selects the highest-reward issued action:

```text
h(W) = argmax_j X_j
```

Closed form:

```text
rho_K = P[max_j X_j > 0.96] = 1 - 0.96^K
```

At `K=16`, local Monte Carlo gives:

| Method | False certification | Yield | Reward |
|---|---:|---:|---:|
| global CP | 0.479055 | 1.000000 | 0.941323 |
| reward-bin UCB, 50 bins | 0.000000 | 1.000000 | 0.901374 |
| CRC-style threshold auditor | 0.032165 | 1.000000 | 0.903426 |
| ACCS-v0 finite-rule auditor | 0.032165 | 1.000000 | 0.903426 |
| oracle tau=0.96 | 0.000000 | 1.000000 | 0.901374 |

Interpretation:

```text
The toy strongly supports the phenomenon: marginal proposal calibration is not
selected-claim calibration. It does not by itself establish unique ACCS method
novelty, because reward-bin and CRC-style baselines also repair this toy.
```

Primary assets:

```text
analysis/paper_assets/figure1_selection_amplification_hardened.pdf
analysis/paper_assets/table_toy_k16.csv
```

---

## 2. Policy-Mismatch Toy

Construction:

```text
The same first action is followed by two possible continuation policies.
Behavior continuation rescues.
Deployment continuation exploits.
```

At `K=16`:

| Method | False certification | Yield | Reward |
|---|---:|---:|---:|
| behavior-rescue labels | 0.000000 | 1.000000 | 0.941288 |
| deployment-exploit accept-all | 0.814995 | 1.000000 | 0.941288 |
| declared-policy support-aware cap | 0.000000 | 1.000000 | 0.841077 |

Interpretation:

```text
Residual-cost certificates are continuation-policy-specific.
Offline behavior labels do not automatically certify deployment-continuation
claims.
```

Primary assets:

```text
analysis/paper_assets/figure2_policy_mismatch.pdf
analysis/paper_assets/table_policy_mismatch_k16.csv
```

---

## 3. No-Overlap Toy

Construction:

```text
Two worlds are identical on offline support and differ only in unsupported
high-reward actions.
```

At `K=16`:

| World / Method | False certification | Yield | Reward |
|---|---:|---:|---:|
| M0 safe unsupported / naive certify | 0.000000 | 1.000000 | 0.941092 |
| M1 unsafe unsupported / naive certify | 0.814225 | 1.000000 | 0.941092 |
| M1 unsafe unsupported / support-aware cap | 0.000000 | 1.000000 | 0.841366 |

Interpretation:

```text
Unsupported high-reward actions cannot receive distribution-free safety
certificates from offline evidence alone. Support-aware abstention or capping
is an evidence requirement, not a cosmetic conservative option.
```

Primary assets:

```text
analysis/paper_assets/figure3_no_overlap.pdf
analysis/paper_assets/table_no_overlap_k16.csv
```

---

## 4. Supported Claims

Supported locally:

1. Marginal proposal-level calibration can fail dramatically after action selection.
2. The right primary metric is false certification among issued action claims.
3. The exact toy is a phenomenon test, not a unique ACCS method-novelty proof.
4. Residual-cost certification is continuation-policy-specific.
5. Unsupported actions require support-aware abstention, capping, or additional assumptions.

Still pending:

1. Strong safe-RL systems such as CAPS or SafeFQL exhibit the same selected-claim gap.
2. ACCS improves over strong selective baselines on realistic query banks.
3. Weighted/off-policy auditing works beyond toys.
4. Action-level certificates improve episode-level outcomes.

---

## 5. Local Verdict

The local package is positive for the paper's high-level thesis:

```text
Safe action learning and safe action certification are different problems.
```

The local package also prevents overclaiming:

```text
The first figure should sell the estimand and phenomenon.
The method novelty must be built on RL-specific support, off-policy, and
continuation-policy structure.
```
