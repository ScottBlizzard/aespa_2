# Theoretical Foundations: Calibration After Action Selection

> **Last updated**: 2026-06-23  
> **Goal**: Replace the earlier marginal-coverage theory with a selection-aware theory target.  
> **Current verdict**: ordinary group/Mondrian conformal coverage is not enough for the paper's intended action-certificate claim.

---

## 0. Executive Summary

The theory must now support a narrower and harder thesis:

```text
A learned cost or feasibility estimate is not a calibrated deployment certificate.
```

The paper should not claim that ACCS solves safe RL, nor that marginal conformal coverage automatically controls accepted actions. It should claim:

1. **The target is false certification among issued claims.** The main risk is not prediction interval width; it is executing actions whose certified safety claims are false.
2. **Selection matters.** A conformal bound can have valid marginal coverage over proposals while failing badly after the deployment system selects the highest-reward certified action.
3. **The residual-cost target is policy-specific.** A certificate for `Z_H` must state the continuation policy under which `Z_H` is defined.
4. **No support means no nontrivial claim.** If the calibration distribution has insufficient overlap with a queried state-action region, a valid distribution-free auditor must abstain.
5. **CAPS/SafeFQL/AEGIS/BCRL are action-feasibility prior work.** The remaining theory gap is finite-data auditing after selection, not inventing feasible action sets.

---

## 1. Formal Setup

Let an offline dataset be:

```text
D = {(s_t, a_t, r_t, c_t, s_{t+1})}
```

A base method proposes candidate actions:

```text
C(s) = {a_1, ..., a_K}
```

The base method may be a learned policy, CAPS-style policy switching, a reachability method, SafeFQL, BCRL, or another offline safe RL score.

For a candidate action `a`, the residual safety target must include the continuation policy:

```text
Z_H^{pi_cont}(s,a) = sum_{t=0}^{H-1} c_t
```

where the first action is `a` and subsequent actions follow the declared continuation policy `pi_cont`. This continuation policy may be:

1. the original base policy;
2. a CAPS switching policy;
3. an ACCS shielded policy;
4. a fixed fallback;
5. a simulator-branching evaluation policy.

The certification target is not ordinary marginal prediction coverage. It is false certification among issued claims:

```text
FCR_issued = P[Z_H^{pi_cont}(s,a) > b | certificate issued for (s,a,b)]
```

or a finite-sample / high-probability analogue over a stream of issued claims.

---

## 2. Why the Old Proposition 2 Was Invalid

The earlier theory used a conformal upper bound:

```text
P[Z <= U] >= 1 - alpha
```

and accepted an action when:

```text
U <= b
```

This only implies:

```text
P[{U <= b} and {Z > b}] <= P[Z > U] <= alpha
```

It does **not** imply:

```text
P[Z > b | U <= b] <= alpha
```

The available bound is:

```text
P[Z > b | U <= b] <= alpha / P[U <= b]
```

If only 10% of queries are accepted and all marginal conformal failures concentrate inside that accepted 10%, marginal coverage can be 95% while accepted-claim failure is 50%.

This is the central statistical problem:

```text
calibration after deployment-time action selection
```

---

## 3. Proposition 1: Group-Marginal Coverage

### Claim

Within a fixed group, split conformal gives group-marginal upper-cost coverage under exchangeability.

### Statement

For group `g`, calibration scores are:

```text
e_i = Z_i^{pi_cont} - Q_c_hat(s_i,a_i),  where G(s_i,a_i)=g
```

Let `q_g` be the finite-sample conformal quantile and define:

```text
U_g(s,a,alpha) = Q_c_hat(s,a) + q_g
```

If calibration examples and the new proposal query are exchangeable conditional on `G(s,a)=g`, then:

```text
P[Z_H^{pi_cont}(s,a) <= U_g(s,a,alpha) | G(s,a)=g] >= 1 - alpha
```

### Boundary

This is correct but not novel. It is a calibration primitive, not the main theorem. It does not control false certification after selecting among multiple candidates or budgets.

### Empirical Prediction

Before selection, global/group conformal should achieve nominal marginal coverage. After selection, false certification among issued claims can be much higher.

---

## 4. Proposition 2: Selection Can Concentrate Calibration Failures

### Claim

Marginally valid conformal bounds can be badly miscalibrated among selected or issued action claims.

### Construction Sketch

At a state `s`, suppose there are `K` candidate actions. Each candidate has a conformal upper bound that is marginally valid at level `1-alpha` over the proposal distribution. The deployment rule selects:

```text
a_selected = argmax_a Q_r(s,a) subject to U(s,a) <= b
```

If residual-cost errors correlate with reward or with the selection score, the selected subset can concentrate the conformal failures. The pooled marginal failure rate remains at most `alpha`, but:

```text
P[Z_H^{pi_cont}(s,a_selected) > b | certificate issued] >> alpha
```

### Empirical Prediction

An exact toy should show:

1. nominal marginal coverage over all proposals;
2. large false certification among selected actions;
3. failure rate increasing with candidate set size `K`;
4. correction by a selection-aware method or a conservative risk-control baseline.

### Evidence Status

This is the next required Phase 1 artifact.

---

## 5. Proposition 3: Policy-Specific Residual Cost Target

### Claim

Residual-cost certificates are only meaningful for the continuation policy under which residual cost is defined and calibrated.

### Statement

In general:

```text
Z_H^{beta}(s,a) != Z_H^{pi_cont}(s,a)
```

where `beta` is the behavior policy that generated offline trajectories and `pi_cont` is the deployment continuation policy. Calibration labels collected under `beta` do not automatically calibrate certificates for `pi_cont`.

### Consequence

Before implementation, the project must choose one of:

1. calibrate using target-continuation rollouts generated by simulator branching;
2. use valid off-policy conformal/OPE machinery with overlap assumptions;
3. use a model-based residual-cost target with explicit model-error treatment;
4. weaken the target to one-step safety cost if residual horizon labels are not identifiable.

### Evidence Status

Pending. This must be settled before broad benchmark work.

---

## 6. Proposition 4: No-Overlap Impossibility

### Claim

Without calibration support for a queried state-action region, no distribution-free certifier can issue a nontrivial valid safety claim.

### Statement

If a deployment state-action region has zero or insufficient probability under the calibration distribution, there exist two CMDPs that induce the same offline data distribution and aggregate evaluation statistics but assign opposite residual-cost outcomes to the unsupported deployment action. Any certifier that issues the same nontrivial certificate in both worlds must fail in one of them.

### Proof Sketch

Because the offline data distribution is identical in the unsupported region, the certifier receives no information distinguishing the two worlds. If it certifies the unsupported action as safe, one world can assign high residual cost to that action while preserving all observed data. Therefore distribution-free validity requires abstention or fallback when support is insufficient.

### Empirical Prediction

In support stress tests, claim yield should fall and abstention should rise before false certification rises. If a method continues issuing claims in unsupported regions, false certification should increase.

---

## 7. Target Theorem: Selection-Aware False Certification Control

### Desired Claim

ACCS should control false certification among issued claims, not only marginal prediction coverage over all proposals.

### Target Statement

For declared proposal distribution, continuation policy, grouping rule, budget range, and support assumptions, prove a statement of the form:

```text
With probability at least 1 - delta over calibration data,
sup_{g in G} sup_{b in B}
P[Z_H^{pi_cont}(s,a) > b | certificate issued, G(s,a)=g, b] <= alpha
```

or a false-coverage-rate analogue over issued claims:

```text
E[# false issued claims / max(1, # issued claims)] <= alpha
```

### Required Assumptions

The theorem must explicitly state:

1. proposal distribution;
2. selection rule;
3. continuation policy;
4. budget query rule;
5. group construction;
6. minimum support / overlap;
7. trajectory dependence treatment;
8. fallback behavior when support is insufficient.

### Baseline Theory To Compare

The method should be compared against:

1. global split conformal;
2. group/Mondrian split conformal;
3. conformal risk control;
4. selective conformal / FCR control;
5. no-overlap abstention rule.

---

## 8. Budget Monotonicity

### Claim

For fixed calibrated certificates, the certified action set is monotone in the deployment budget.

### Statement

Let:

```text
A_cert(s,b,alpha) = {a : U(s,a,alpha) <= b}
```

If `b1 <= b2`, then:

```text
A_cert(s,b1,alpha) subseteq A_cert(s,b2,alpha)
```

### Boundary

This is useful for implementation and figures, but it is not a major theorem. The major theorem must address selection-aware false certification, not set nesting.

---

## 9. Horizon-Level Boundary

### Claim

Action-claim calibration does not automatically imply full trajectory safety.

### Statement

Even if each issued one-step or residual-cost claim is controlled under stated assumptions, the executed policy can change the state distribution over time. If sequential deployment violates the proposal/continuation/support assumptions, action-level validity may degrade.

### Required Evaluation

Report:

1. false certification among issued claims;
2. episode budget violation rate and magnitude;
3. time to first violation;
4. fallback usage;
5. calibration drift over horizon;
6. support diagnostics over time.

---

## 10. Claim-Evidence Constraints

Paper writing must obey:

1. Do not claim accepted-action risk control from ordinary marginal conformal coverage.
2. Do not claim individual-action validity; say action-specific reports with group-/selection-level validity.
3. Do not hide the continuation policy in `Z_H`.
4. Do not claim distribution-free validity outside calibration support.
5. Do not claim to be first conformal offline safe RL; SafeFQL exists.
6. Do not claim CAPS is merely policy-level; CAPS filters actions.
7. Do not use unsupported safety success as a headline metric unless an external simulator-ground-truth auditor defines it.

---

## 11. Theory-To-Experiment Map

| Theory claim | Required experiment | Status |
|---|---|---|
| marginal conformal can fail after selection | exact toy with selected-action false certification | pending |
| selection-aware control can repair false certification | toy with global/group/CRC/selective/ACCS comparison | pending |
| residual-cost target is policy-specific | simulator branching under declared continuation policy | pending |
| no overlap requires abstention | support stress test | pending |
| budget monotonicity | budget sweep over fixed certificates | pending |
| horizon boundary | episode-level audit and fallback metrics | pending |
| CAPS still needs finite-data auditing | CAPS vs CAPS+global/group/selective ACCS | pending |
