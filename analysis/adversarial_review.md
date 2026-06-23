# Adversarial Review

> **Last updated**: 2026-06-23  
> **Purpose**: Maintain a skeptical reviewer view before the paper is written.

---

## Reviewer-Level Verdict

Current status:

```text
Promising thesis, no experimental evidence yet.
The oral ceiling depends on whether Phase 1 produces a clean selection-failure phenomenon:
marginal calibration can be nominal over proposals while false certification is high among selected actions.
```

Main risk:

```text
If results only show small reward/violation improvements, the work may be judged as
a natural conformal safe RL combination rather than a methodology paper.
```

After the external review, the paper must convince reviewers that:

```text
Learned cost or feasibility estimates are not calibrated deployment certificates.
Existing action-feasibility methods still need finite-data auditing after selection.
```

---

## Rejection Risks

| Risk | Severity | Current defense | Needed action |
|---|---:|---|---|
| SafeFQL already combines conformal calibration and offline safe RL | Critical | Added to literature gate | Reframe around post-selection false certification and compare if feasible |
| CAPS already solves changing constraints | Critical | Reframed as action-claim provenance, not policy switching | CAPS vs CAPS+ACCS experiment |
| Accepted-action theorem is mathematically wrong | Critical | Old Proposition 2 removed | Prove or benchmark selection-aware false-certification control |
| Residual-cost target is policy-specific | Critical | `Z_H^{pi_cont}` added to theory | Define continuation policy and label source before coding |
| Looks like conformal prediction + safe RL | High | Reframed as calibration after action selection | Exact selection-failure main phenomenon + strong intro |
| Action-level theorem too weak for RL | High | Explicit `C` vs `H` separation | Horizon audit and careful wording |
| Baselines incomplete | High | Baseline list planned | Implement fair comparisons |
| No-overlap/abstention is product feature, not theorem | High | No-overlap impossibility planned | Exact support stress test and theorem |
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
  - define calibration after action selection early;
  - define false certification among issued claims;
- define `U/C/A/H` early;
- method section must explain why action conditioning matters;
- theorem section must not overclaim horizon safety.

Status: blueprint ready, paper not drafted.

### 3. Experimental Strength

Required:

- exact selection-failure toy main phenomenon;
- Safety-Gymnasium main table;
- strong baselines;
- CAPS and CAPS+ACCS;
- SafeFQL;
- conformal risk control and selective/FCR baselines;
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
ACCS targets false certification among action claims issued after deployment-time action selection.
ACCS is a selection-aware auditor that can wrap strong offline safe RL policies.
Horizon-level safety is evaluated through conservative risk allocation and empirical audits.
```

Avoid:

```text
ACCS guarantees safe trajectories.
ACCS solves deployment shift.
ACCS is distribution-free under policy-induced state shift.
ACCS is the first method for changing safety constraints.
ACCS beats CAPS as a policy optimizer.
ACCS is the first conformal offline safe RL method.
Marginal conformal coverage controls accepted-action risk.
```

---

## Next Review Gate

After Phase 1:

1. Does ordinary global/group conformal achieve nominal marginal coverage over proposals?
2. Does selected-action false certification exceed alpha substantially?
3. Does the failure worsen with candidate-set size K?
4. Does selection-aware ACCS or selective/FCR baseline restore target false certification?
5. Is claim yield nontrivial in supported regions?
6. Do unsupported regions trigger abstention/fallback before false certification rises?
7. Does the result justify moving to CAPS/SafeFQL comparisons?

If any answer is no, revise experiment design before scaling.
