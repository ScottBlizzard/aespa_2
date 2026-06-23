# Theoretical Foundations: Action-Safety Claims under Moving Constraints

> **Last updated**: 2026-06-23  
> **Goal**: Organize AAAI_2 theory like the stronger reference projects: definitions, assumptions, propositions, proof sketches, empirical predictions, and evidence status.  
> **Core framework**: utility `U`, calibration `C`, adaptivity `A`, and horizon risk `H` are distinct evidence axes.

---

## 0. Executive Summary

The theory should not claim that ACCS solves safe RL. It should claim something narrower and defensible:

1. **Safety is a claim, not a cost.** A deployed action needs calibration evidence and provenance; aggregate episode cost is not enough.
2. **Utility is not safety evidence.** High reward under one budget does not certify a new budget.
3. **Calibration is action-conditional.** A cost bound must be calibrated against the relevant action/risk group.
4. **Adaptivity is budget filtering over a certificate surface, not retraining.** Once upper cost certificates are calibrated, new budgets can be handled by re-filtering actions.
5. **Action-level coverage is not trajectory-level safety.** Horizon risk requires separate assumptions or empirical audit.
6. **Abstention is part of the claim protocol.** Sparse or OOD action groups should fail closed rather than pretending to be safe.

---

## 1. Formal Setup

Let an offline dataset be:

```text
D = {(s_t, a_t, r_t, c_t, s_{t+1})}
```

A base offline policy is:

```text
pi_0(a | s)
```

For a candidate first action `a`, define residual horizon cost:

```text
Z_H(s,a) = sum_{t=0}^{H-1} c_t
```

where the first action is `a` and subsequent actions follow a fixed execution policy or fallback convention.

A cost model predicts:

```text
Q_c_hat(s,a) ≈ E[Z_H(s,a)]
```

A shield accepts an action under deployment budget `b` if:

```text
U_c(s,a,alpha) <= b
```

where `U_c` is a conformal upper cost certificate.

A deployment-time safety claim is:

```text
Claim(s, a, b, alpha, provenance):
    Z_H(s,a) <= b with miscoverage <= alpha
```

where `provenance` records the group, calibration sample size, cost estimate, conformal radius, upper certificate, requested budget, and fallback/abstention reason.

The budget-uniform certificate surface is:

```text
U_c(s,a,alpha)
```

and a deployment budget only thresholds this surface:

```text
A_cert(s,b,alpha) = {a : U_c(s,a,alpha) <= b}
```

---

## 2. Evidence Axes

| Axis | Meaning | Claim boundary |
|---|---|---|
| `U` utility retention | reward after shielding | high reward does not imply safety |
| `C` calibration | action cost upper bound coverage | action-level only under assumptions |
| `A` adaptivity | new budget handled without retraining | budget filtering, not new policy learning |
| `H` horizon risk | episode-level violation behavior | requires separate audit |
| `P` provenance | evidence attached to accepted claims | no provenance means no deployable claim |

Hierarchy:

```text
U does not imply C.
C at one budget does not imply A across budgets.
Action-level C does not imply H.
Aggregate cost does not imply P.
```

---

## 3. Proposition 1: Action-Conditional Coverage

### Claim

Within a fixed action/risk group, conformal calibration gives a finite-sample upper cost certificate under group-conditional exchangeability.

### Setup

For group `g`, calibration scores are:

```text
e_i = Z_i - Q_c_hat(s_i,a_i),  where G(s_i,a_i)=g
```

Let `q_g` be the finite-sample conformal quantile:

```text
q_g = Quantile_{ceil((n_g+1)(1-alpha))/n_g}({e_i})
```

Define:

```text
U_c(s,a,alpha) = Q_c_hat(s,a) + q_g
```

### Statement

If calibration examples and the deployment query are exchangeable conditional on `G(s,a)=g`, then:

```text
P[Z_H(s,a) <= U_c(s,a,alpha) | G(s,a)=g] >= 1 - alpha
```

up to the usual finite-sample conformal convention.

### Proof Sketch

By exchangeability, the rank of the new score among the calibration scores plus the new score is uniform. Choosing the conformal quantile at level `1-alpha` gives marginal group-conditional coverage for the new score, hence for `Z_H`.

### Empirical Predictions

1. Group-wise empirical coverage should be near or above `1-alpha`.
2. Global conformal should over-cover low-risk groups and may be unnecessarily conservative.
3. Very small groups should have unstable quantiles and require fallback/abstention.

### Evidence Status

Pending Phase 1/2.

---

## 4. Proposition 2: Certified Action Implies Budget Violation Control

### Claim

If ACCS accepts an action because its conformal upper bound is below budget, then action-level budget violation risk is controlled at the calibration level.

### Statement

If:

```text
U_c(s,a,alpha) <= b
```

then under Proposition 1 assumptions:

```text
P[Z_H(s,a) > b | G(s,a)=g] <= alpha
```

for the accepted action query.

### Proof Sketch

The event `Z_H(s,a) > b` implies `Z_H(s,a) > U_c(s,a,alpha)` whenever `U_c <= b`. Proposition 1 bounds the latter event by `alpha`.

### Empirical Predictions

1. Accepted actions should have low budget exceedance under held-out test rollouts.
2. Undercoverage should concentrate in OOD or sparse groups.
3. ACCS reports should identify which group and quantile supported each accepted action.

### Evidence Status

Pending Phase 2/3.

---

## 5. Proposition 3: Budget Monotonicity

### Claim

For fixed calibrated upper bounds, the certified action set is monotone in the deployment budget.

### Statement

Let:

```text
A_cert(s,b,alpha) = {a : U_c(s,a,alpha) <= b}
```

If `b1 <= b2`, then:

```text
A_cert(s,b1,alpha) subseteq A_cert(s,b2,alpha)
```

### Proof Sketch

Every action satisfying `U_c <= b1` also satisfies `U_c <= b2`.

### Empirical Predictions

1. Certified action coverage should increase as budget relaxes.
2. Reward should improve as the shield admits more actions.
3. Adaptation to a new budget should require re-filtering, not retraining.

### Evidence Status

Pending Phase 1.

---

## 6. Proposition 4: Calibration Granularity Tradeoff

### Claim

Finer action groups can reduce conservatism but increase quantile variance and abstention risk.

### Statement

If groups are refined, within-group score variance may decrease, but group sample size `n_g` also decreases. When `n_g` is too small, conformal quantiles become unstable or unavailable. Therefore a robust protocol needs hierarchical fallback:

```text
state-action group -> action group -> risk group -> global -> abstain
```

### Proof Sketch

This is a bias-variance/support tradeoff. Finer conditioning better matches the target action distribution but reduces calibration support. Without sufficient samples, finite-sample quantiles are high-variance and may fail closed.

### Empirical Predictions

1. Granularity sweep should show a Pareto curve.
2. Too coarse groups are conservative.
3. Too fine groups increase fallback/abstention.

### Evidence Status

Pending Phase 2.

---

## 7. Proposition 5: Horizon-Level Boundary

### Claim

Action-level coverage does not automatically imply trajectory-level safety under policy-induced distribution shift.

### Statement

If each step `t` satisfies the relevant exchangeability condition and uses miscoverage `alpha_t`, then:

```text
P[any action-level certificate fails over horizon] <= sum_t alpha_t
```

by union bound. If:

```text
sum_t alpha_t <= alpha_episode
```

then certificate failure probability is bounded by `alpha_episode`.

However, if shield-induced actions move the state distribution outside calibration support, the stepwise exchangeability condition can fail.

### Proof Sketch

The first part is a union bound over stepwise certificate failure events. The second part is a limitation: the conformal guarantee is conditional on exchangeability of queried state-action pairs, which sequential shielding can violate.

### Empirical Predictions

1. Per-step coverage and episode violation can diverge.
2. Coverage drift may increase with horizon length.
3. Shift detectors, residual-budget policies, or online recalibration can reduce but not eliminate this boundary.

### Evidence Status

Pending Phase 5/6.

---

## 8. Proposition 6: Aggregate Safety Does Not Identify Claim Support

### Claim

Aggregate reward/cost under a fixed budget cannot determine whether deployment-time action safety claims are supported.

### Statement

There exist two policies or MDP instances with the same aggregate episode cost distribution under a reported evaluation budget, but with different residual action-cost distributions for the state-action queries encountered under a deployment constraint. Any evaluator that observes only aggregate fixed-budget cost cannot distinguish whether the deployment actions have calibrated claim support.

### Proof Sketch

Construct two policies with identical total cost under the evaluation distribution. In one policy, cost is spread across action groups represented in calibration data; in the other, cost is concentrated in rare or unsupported action groups that appear at deployment. Aggregate cost is identical, but action-level conformal provenance differs. Therefore the missing action-claim evidence is not recoverable from the aggregate metric.

### Empirical Predictions

1. A toy deployability-gap construction should show similar episode cost but different claim yield.
2. Unsupported safety success should be nonzero for methods that pass aggregate budgets without certificates.
3. ACCS should expose the gap through abstention or low claim yield rather than silently passing.

### Evidence Status

Pending Phase 1.

---

## 9. Proposition 7: Global Marginal Calibration Is Not Enough for Action Claims

### Claim

Global conformal calibration can be marginally valid while failing to provide useful action-level claim provenance.

### Statement

If two action groups have different residual-cost distributions, a single global quantile either over-covers low-risk groups and reduces certified utility, or fails to provide group-specific evidence needed to issue action-level claims for high-risk groups. Action-level claim validity therefore requires conditioning or a declared fallback/abstention path.

### Proof Sketch

Global conformal controls the rank of a pooled score. Pooled coverage does not imply that each action group has an interpretable, group-specific certificate. If the high-risk group controls the global quantile, low-risk groups become unnecessarily conservative. If the low-risk group dominates the pool, high-risk action claims can be poorly diagnosed. In both cases, the pooled threshold is not an adequate provenance object for a particular action claim.

### Empirical Predictions

1. Global conformal should have lower certified utility area than ACCS at matched miscoverage.
2. Group-wise coverage and claim yield should reveal which groups are over-covered or unsupported.
3. CAPS + global conformal should still lack the provenance quality of CAPS + ACCS.

### Evidence Status

Pending Phase 1/2.

---

## 10. Claim-Evidence Constraints

Paper writing must obey:

1. Do not claim full trajectory safety from action-level theorem.
2. Do not claim distribution-free safety under policy shift.
3. Do not report reward without violation, claim yield, claim miscoverage, abstention, and certified utility.
4. Do not hide sparse groups or fallback decisions.
5. Do not use test budgets or test rollouts to tune group construction.
6. Do not call ACCS "retraining-free" without reporting calibration and inference cost.
7. Do not treat CAPS as background; it is the direct competitor and should be tested with and without ACCS.

---

## 11. Theory-to-Experiment Map

| Theory claim | Experiment | Status |
|---|---|---|
| action-conditional coverage | group-wise coverage table | pending |
| accepted action risk control | accepted-action violation audit | pending |
| budget monotonicity | unseen budget sweep | pending |
| granularity tradeoff | group granularity sweep | pending |
| horizon boundary | per-step vs episode audit | pending |
| abstention as fail-closed protocol | sparse/OOD action stress test | pending |
| aggregate safety does not imply claim support | deployability-gap toy | pending |
| global marginal calibration lacks provenance | global vs ACCS certified utility | pending |
| strong policies still need evidence layer | CAPS vs CAPS+ACCS | pending |
