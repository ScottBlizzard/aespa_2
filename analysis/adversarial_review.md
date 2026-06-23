# Adversarial Review

> **Last updated**: 2026-06-23  
> **Purpose**: Maintain a skeptical reviewer view before the paper is written.

---

## Reviewer-Level Verdict

Current status:

```text
Promising thesis, no experimental evidence yet.
The oral ceiling depends on whether Phase 1/3 produce a clean deployability-gap phenomenon:
aggregate safety can pass while action-level claim support fails.
```

Main risk:

```text
If results only show small reward/violation improvements, the work may be judged as
a natural conformal safe RL combination rather than a methodology paper.
```

After the oral upgrade, the paper must convince reviewers that:

```text
Safety is a claim, not a cost.
Existing policy optimizers or policy switchers still need a deployment evidence layer.
```

---

## Rejection Risks

| Risk | Severity | Current defense | Needed action |
|---|---:|---|---|
| CAPS already solves changing constraints | Critical | Reframed as action-claim provenance, not policy switching | CAPS vs CAPS+ACCS experiment |
| Looks like conformal prediction + safe RL | High | Reframed as budget-uniform action certificate protocol | Deployability-gap main phenomenon + strong intro |
| Action-level theorem too weak for RL | High | Explicit `C` vs `H` separation | Horizon audit and careful wording |
| Baselines incomplete | High | Baseline list planned | Implement fair comparisons |
| Deployability gap seems obvious | High | Need negative construction + Figure 1 showing aggregate pass but unsupported actions | Toy construction and theorem |
| Grouping arbitrary | Medium/High | Granularity and fallback planned | Group sweep and diagnostics |
| Abstention hides failure | Medium | Report abstention as claim discipline | Abstention reason table |
| Reward losses too large | Medium | Risk-utility frontier planned | Matched-risk plots |
| Shift breaks coverage | Medium | Treat as boundary | Shift audit and recalibration |
| Experiment too toy-like | Medium | Safety-Gym/DSRL planned | Do not stop at toy |

---

## Five-Dimension Self-Review

### 1. Contribution

Question:

```text
What new knowledge does the paper give?
```

Current answer:

```text
It argues that aggregate safe RL evaluation cannot issue deployable action safety claims.
It proposes a budget-uniform certificate protocol that attaches calibration provenance
to accepted actions and abstains when evidence is insufficient.
```

Status: needs experimental support.

### 2. Writing Clarity

Required:

- first paragraph must state the safety-claim gap, not only fixed-budget failure;
- define deployability gap and claim provenance early;
- define `U/C/A/H` early;
- method section must explain why action conditioning matters;
- theorem section must not overclaim horizon safety.

Status: blueprint ready, paper not drafted.

### 3. Experimental Strength

Required:

- deployability-gap toy main phenomenon;
- Safety-Gymnasium main table;
- strong baselines;
- CAPS and CAPS+ACCS;
- group-wise coverage;
- ablations.

Status: pending.

### 4. Evaluation Completeness

Required:

- no shield;
- CAPS;
- CAPS+ACCS;
- global conformal;
- global conformal over CAPS;
- state-only conformal;
- action/state-action ACCS;
- ensemble pessimism;
- offline safe RL baselines;
- optional retrain upper bound.

Status: pending.

### 5. Method Soundness

Required:

- strict train/calibration/test split;
- no test-tuned groups;
- finite-sample quantile formula;
- report sparse groups;
- fail closed under insufficient evidence.

Status: pending.

---

## Paper-Safe Wording

Use:

```text
ACCS issues action-level safety claims with finite-sample coverage under group-conditional exchangeability.
ACCS is a deployment evidence layer that can wrap strong offline safe RL policies.
Horizon-level safety is evaluated through conservative risk allocation and empirical audits.
```

Avoid:

```text
ACCS guarantees safe trajectories.
ACCS solves deployment shift.
ACCS is distribution-free under policy-induced state shift.
ACCS is the first method for changing safety constraints.
ACCS beats CAPS as a policy optimizer.
```

---

## Next Review Gate

After Phase 1:

1. Can aggregate budget success hide low action-claim support?
2. Is unsupported safety success nontrivial?
3. Is global conformal visibly over-conservative in certified utility / claim yield?
4. Does ACCS improve certified utility at matched claim miscoverage?
5. Are group-wise coverage diagnostics and provenance reports clean?
6. Is abstention interpretable rather than overwhelming?
7. Does the result motivate CAPS+ACCS rather than merely ACCS alone?

If any answer is no, revise experiment design before scaling.
