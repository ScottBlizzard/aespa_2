# Strong Proposer Pilot Protocol

Updated: 2026-06-23

This protocol must be frozen before any server experiment. Its purpose is to keep the first non-toy run aligned with the paper's actual claim: selected-action safety certification, not generic reward/cost optimization.

---

## 1. First Pilot Choice

Use a staged pilot order:

```text
1. synthetic OSRL-style candidate bank generated locally or cheaply on server;
2. CAPS single-task integration;
3. SafeFQL pilot only after query-bank and residual-label machinery is stable.
```

The lowest-friction first non-toy proposer should satisfy:

- can generate `K` candidate actions per state;
- exposes reward/cost or feasibility scores;
- can run with fixed random seeds;
- allows state restore or branch rollouts for residual labels;
- can share the same query bank across auditors.

Do not start with the hardest SafeFQL integration unless the environment and code are already stable.

---

## 2. Frozen Query-Bank Schema

Every proposer must export a fixed query bank:

```text
QueryBlock = {
  "query_id": str,
  "env_id": str,
  "dataset_id": str,
  "state": array or state_ref,
  "budget": float,
  "candidate_actions": array[K, action_dim],
  "reward_scores": array[K],
  "cost_scores": array[K],
  "safety_scores": array[K],
  "support_scores": array[K],
  "proposer_name": str,
  "proposer_checkpoint": str,
  "continuation_policy": str,
  "fallback_policy": str,
  "seed": int
}
```

All auditors must consume exactly the same query bank:

```text
none / original proposer
global CP
group or rank CP
reward-bin/rank-bin baseline
CRC-style/selective baseline
ACCS-v0 / support-aware ACCS
```

No auditor may change the proposer distribution. Otherwise risk-yield comparisons become invalid.

---

## 3. Residual-Label Protocol

The residual target must be declared before running:

```text
Z_H^{pi_cont}(s,a)
```

Allowed label protocols:

1. **Simulator branching.**
   - Restore state `s`.
   - Execute candidate action `a`.
   - Continue with declared `pi_cont`.
   - Run `M` stochastic branches.
   - Estimate residual violation or residual-cost quantile.
   - Paper wording: simulator-assisted auditing.

2. **One-step observable target.**
   - Use immediate cost after candidate action.
   - Lower ambition but clean identification.
   - Useful for first pilot if simulator branching is hard.

3. **Off-policy weighted audit.**
   - Requires behavior/target density ratio or propensity estimate.
   - Requires effective sample size and support threshold.
   - Do not use unless weights can be diagnosed.

4. **Model-based residual target.**
   - Requires dynamics/cost model.
   - Must report model uncertainty and support diagnostics.

For the first pilot, prefer:

```text
simulator branching if state restore is available;
otherwise one-step observable target.
```

---

## 4. Split Protocol

Use four disjoint splits:

```text
train
tune/calibration
audit
test
```

Rules:

- train proposer and score models only on `train`;
- choose groups, bins, thresholds, and rule family before `audit` outcomes;
- select ACCS-v0 rule on `audit`;
- report final numbers only on `test`;
- keep query-bank generation fixed before auditor comparison.

---

## 5. Metrics

Primary metrics:

```text
selected_false_certification = sum false issued / sum issued
claim_yield = sum issued / number of query blocks
normalized_reward
fallback_rate
fallback_reward
support_rejection_rate
episode_violation_rate if horizon rollouts are available
```

Report all metrics together. A method that controls risk by issuing no claims is not a useful certifier.

---

## 6. Minimum Baseline Matrix

For the first non-toy pilot:

| Proposer | Auditors |
|---|---|
| synthetic / easy OSRL proposer | none, global CP, reward-bin/rank-bin, CRC-style, ACCS-v0 |
| CAPS single task | CAPS original, CAPS+global CP, CAPS+reward-bin/rank-bin, CAPS+CRC-style, CAPS+ACCS |
| SafeFQL pilot | SafeFQL original calibration, SafeFQL+post-selection audit, SafeFQL+ACCS |

The first server pilot does not need all three proposers. It needs one proposer with a clean query bank and residual labels.

---

## 7. Expected Output Contract

First server pilot output:

```text
outputs/phase_strong_proposer_pilot_server.json
outputs/phase_strong_proposer_pilot_server.md
```

Required JSON fields:

```text
{
  "protocol_version": "2026-06-23",
  "proposer": "...",
  "env": "...",
  "splits": {...},
  "query_bank": {...},
  "residual_label_protocol": "...",
  "auditors": [
    {
      "name": "...",
      "selected_false_certification": float,
      "claim_yield": float,
      "normalized_reward": float,
      "fallback_rate": float,
      "support_rejection_rate": float,
      "episode_violation_rate": float or null
    }
  ]
}
```

---

## 8. Go / No-Go

Go to broader server benchmarks only if:

- the phenomenon survives on a non-toy query bank;
- global/marginal audit fails or is clearly less useful than selected audit;
- the strongest local baseline does not fully dominate ACCS;
- claim yield remains useful;
- residual-label protocol is defensible in paper wording.

No-go or pivot if:

- reward-bin/rank-bin fully dominates ACCS on realistic query banks;
- selected-claim risk is already controlled by original CAPS/SafeFQL calibration;
- residual labels require an oracle too strong to claim offline auditing;
- episode-level outcomes do not reflect any action-level improvement.
