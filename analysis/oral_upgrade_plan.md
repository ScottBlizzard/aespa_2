# Oral Upgrade Plan

> Last updated: 2026-06-23  
> Purpose: upgrade AAAI_2 from a solid AAAI paper into an oral-ambition paper after the Phase 0 literature gate.

## Status After External Review

This file records the first oral-upgrade attempt. It has been partially superseded by `AI_Safety_Thesis_Review.md` and the follow-up edits on 2026-06-23.

The current preferred route is no longer the broad slogan:

```text
Safety is a claim, not a cost.
```

The current preferred route is:

```text
Calibration After Action Selection:
learned safe-RL scores can be marginally calibrated before deployment,
but false certification can concentrate among actions selected and executed
under candidate-action and moving-budget queries.
```

Keep this file as context, but use `idea_blueprint.md`, `theory_proofs.md`, `NEXT_STEPS.md`, and `analysis/claim_evidence_map.md` as the active route.

## Verdict

The current ACCS route is viable, but the paper must be upgraded from:

```text
action-conditional conformal shield for offline safe RL
```

to:

```text
deployment-time safety claims for offline RL under moving constraints
```

This distinction matters because CAPS, AEGIS, BCRL, and TREBI already cover much of the "adapt to new budget" space. The oral-level opening is not to claim better policy optimization. It is to define a missing evidence object:

```text
Which proposed deployment actions have earned a statistically calibrated safety claim
under the current constraint, and which must be rejected because evidence is absent?
```

## New Core Thesis

Safety is not a scalar property of a policy. Safety is a claim issued about an action under a deployment constraint, with calibration evidence and provenance.

The paper should argue:

```text
Offline safe RL methods can optimize or switch policies across budgets,
but they generally do not say which individual deployment-time actions are
statistically justified under the requested safety constraint.
```

ACCS becomes the constructive answer:

```text
ACCS turns candidate policy actions into budget-uniform, action-level safety claims:
accept, replace, or abstain, with finite-sample calibration provenance.
```

## Stronger Title Options

Preferred:

```text
Safety Is a Claim, Not a Cost: Calibrated Action Certificates for Offline RL under Moving Constraints
```

Safer AAAI-style:

```text
Which Actions Are Safe Enough? Calibrated Action Certificates for Offline Safe Reinforcement Learning
```

Current title remains acceptable but weaker:

```text
When Constraints Move: Action-Conditional Conformal Shields for Offline Safe Reinforcement Learning
```

## Upgrade 1: Safety-Claim Formalism

Define a safety claim as a tuple:

```text
Claim(s, a, b, alpha, provenance):
    executing action a in state s has residual safety cost <= b
    with miscoverage <= alpha under the stated calibration provenance.
```

Each accepted action must carry:

```text
state/action group
calibration sample size
cost estimate
conformal radius
upper cost certificate
requested budget
alpha level
fallback or abstention reason
```

This turns ACCS from a heuristic shield into a claim-issuing protocol.

## Upgrade 2: Budget-Uniform Certificate Surface

The strongest theoretical angle is simultaneous validity over deployment budgets.

Instead of training a policy for each budget, learn a budget-independent certificate surface:

```text
U_c(s,a,alpha)
```

Then every deployment budget is handled by thresholding:

```text
A_cert(s,b,alpha) = {a : U_c(s,a,alpha) <= b}
```

This gives a clean theorem:

```text
Once U_c is calibrated, the same action certificate supports any later budget query.
The certified action sets are nested as b changes.
```

This is the best response to CAPS/BCRL:

- CAPS learns/switches policies for constraints.
- BCRL learns budget-conditioned reachability.
- ACCS learns a budget-uniform evidence surface for issuing action claims.

## Upgrade 3: Deployability Gap Metric

Add a new evaluation object:

```text
Deployability Gap = policy-level budget success - action-level claim support
```

Operational metrics:

| Metric | Meaning |
|---|---|
| Certified Utility Area | area under reward-vs-budget curve using only certified actions |
| Claim Yield | fraction of candidate actions receiving a valid certificate |
| Claim Miscoverage | empirical failure rate among accepted claims |
| Evidence Abstention | fraction rejected due to insufficient calibration support |
| Unsupported Safety Success | episodes that satisfy aggregate cost but contain uncertified actions |

This can make the paper feel like it creates a new evaluation protocol, not just a method.

## Upgrade 4: Necessity / Impossibility Results

The theory should include at least one negative theorem or construction.

### Theorem A: Fixed-budget success does not imply action safety under moved budgets

Construct two MDPs/policies with identical fixed-budget aggregate return/cost but different residual action-cost distributions under a stricter deployment budget. Any evaluation using only aggregate fixed-budget cost cannot distinguish them.

Reviewer-facing message:

```text
The missing evidence is not an implementation detail. It is information-theoretically absent from fixed-budget aggregate evaluation.
```

### Theorem B: Global calibration is insufficient for action claims

Construct two action groups with different residual-cost distributions. A global conformal threshold can be marginally valid but either:

1. over-conservative for low-risk groups, reducing utility; or
2. unable to support group-level claims for high-risk groups.

Reviewer-facing message:

```text
Action safety claims require action-conditional evidence.
```

### Theorem C: Budget-uniform validity after calibration

If the action upper-cost certificate is calibrated once, then post-hoc budget selection preserves validity because the budget only thresholds a precomputed bound.

Reviewer-facing message:

```text
ACCS is not retraining-free by convenience; it has a clean post-hoc query structure.
```

## Upgrade 5: CAPS as a Base Policy, Not Just a Baseline

To avoid a direct novelty collision with CAPS, run:

```text
CAPS
ACCS over single policy
CAPS + ACCS
Global conformal over CAPS
```

If `CAPS + ACCS` improves claim reliability or diagnoses unsupported actions while preserving reward, the paper becomes much harder to reject as "CAPS already did it."

The story becomes:

```text
Even strong constraint-adaptive policies need a deployment evidence layer.
```

## Upgrade 6: Figure 1 Should Be a Claim Failure, Not Just a Budget Failure

Old Figure 1:

```text
fixed-budget policy violates stricter unseen budgets.
```

Upgraded Figure 1:

```text
Two methods both satisfy the aggregate cost budget, but one does so through actions
that have no calibrated support under the deployment constraint.
```

This is much sharper because it attacks a hidden assumption in evaluation:

```text
aggregate episode cost can look safe while action-level safety claims are unearned.
```

## Upgraded Contributions

1. We formulate deployment-time safety in offline RL as a problem of issuing calibrated action-level claims under moving constraints.
2. We identify a deployability gap: fixed-budget aggregate safety can fail to imply action-level claim support under new constraints.
3. We propose ACCS, a budget-uniform conformal certificate protocol that accepts, replaces, or abstains from candidate policy actions.
4. We prove action-conditional coverage, post-hoc budget validity, and limitations of fixed-budget/global evidence.
5. We evaluate not only reward and cost, but certified utility, claim yield, miscoverage, abstention, and horizon risk.
6. We show ACCS can wrap strong offline safe RL competitors, including CAPS-style constraint-adaptive policies.

## Main Experiments After Upgrade

Minimum oral-ambition experiment set:

1. Toy deployability-gap construction.
2. DSRL/Safety-Gym moving-budget benchmark.
3. CAPS vs ACCS vs CAPS+ACCS.
4. Global/state/action conformal comparison.
5. Claim-yield and certified-utility curves over budgets.
6. Sparse/OOD action group abstention stress test.
7. Horizon audit showing what action claims do and do not guarantee.

## Risk

This upgrade raises the ceiling but also raises the burden. The method must produce more than lower violation:

```text
It must produce interpretable claim provenance that competitors do not provide.
```

If the experiments only show better reward-cost tradeoff, the paper will look incremental. If the experiments show a real deployability gap and a useful certificate layer over strong policies, the paper can plausibly aim for oral-level attention.

## Next Decision

Before coding broad benchmarks, rewrite the blueprint around:

```text
Safety claims / certificate surface / deployability gap / CAPS+ACCS
```

Then implement Phase 1 toy with the upgraded Figure 1 target:

```text
aggregate safety can pass while action-level claim support fails.
```
