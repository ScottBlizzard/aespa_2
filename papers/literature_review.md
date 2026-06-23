# Phase 0 Literature Review

> Last updated: 2026-06-23  
> Purpose: decide whether AAAI_2 has enough novelty for an oral-ambition submission before broad experiments.

## Executive Verdict

The naive claim is already taken:

```text
Offline safe RL under changing deployment constraints without retraining.
```

CAPS is the direct prior and must be treated as the first competitor, not background. TREBI, AEGIS, BCRL, Robust Probabilistic Shielding, and SafeFQL also occupy parts of the moving-budget / action-feasibility / conformal-safety space.

The viable AAAI_2 novelty boundary is narrower but still strong:

```text
ACCS is not a generic conformal shield. It must become a selection-aware
finite-data auditor: it controls or diagnoses false certification among
actions actually selected under deployment-time candidate/action/budget queries.
It does not claim to be the first method to identify feasible actions.
```

This framing can still be high-ceiling because it changes the evaluation question:

```text
not "which actions have low learned cost?"
but "after deployment-time action selection, which issued safety claims remain calibrated?"
```

The recommended thesis after the GPTPro review is:

```text
A learned cost or feasibility estimate is not a calibrated deployment certificate.
```

## Direct Competitors

### CAPS: critical threat and primary baseline

CAPS targets the same high-level pain point: deployment constraints can vary after offline training. It also performs action-level candidate filtering at each state using learned cost values and a fallback when no candidate is feasible.

Implication for AAAI_2:

- Do not sell "constraint-adaptive without retraining" as the main novelty.
- Use CAPS as the strongest baseline and probably as a base policy family.
- The ACCS difference must be: finite-data calibration after CAPS-style action selection, not the mere existence of action filtering.

Required experiments:

- ACCS wrapping one fixed policy vs CAPS.
- ACCS wrapping CAPS outputs, if integration is feasible.
- CAPS vs CAPS+global CP vs CAPS+group CP vs CAPS+selection-aware ACCS on false certification among issued claims, claim yield, utility, fallback cost, and episode risk.

### SafeFQL: critical threat

SafeFQL combines reachability-style safe offline RL, deployment-time safe action selection, and conformal calibration of the learned safety boundary. It kills any broad claim that ACCS is the first conformal or finite-sample safety-calibrated offline safe RL method.

Implication for AAAI_2:

- Add SafeFQL as a direct baseline or at least a required ablation target in the exact toy / Safety-Gym setting.
- Claim novelty only where SafeFQL does not directly operate: selection-aware false-certification control under candidate selection, moving budgets, arbitrary base scores, and explicit support abstention.
- Do not claim "first conformal offline safe RL" or "first finite-sample safety certificate."

### AEGIS: critical threat

AEGIS claims almost-sure safety across any feasible budget using feasibility critics and a diffusion policy. It threatens any broad "works for arbitrary budgets" statement.

Implication for AAAI_2:

- Avoid claiming stronger safety than the method proves.
- Position ACCS as a calibration/reporting wrapper that can expose uncertainty rather than a new generative policy.
- Compare against AEGIS if code appears or reproduce the simplest budget-conditioned feasibility baseline.

### BCRL: high threat

BCRL uses budget-conditioned reachability, which is close to a principled "any budget" formulation.

Implication for AAAI_2:

- Do not define novelty as budget conditioning alone.
- Use BCRL to motivate why reachability-style structure is powerful but not the same as conformal action-level evidence.
- Include a reachability or value-threshold baseline if feasible.

### Robust Probabilistic Shielding: high threat

This is the closest shielding-style OSRL competitor found so far. It shifts the literature from policy learning toward runtime intervention.

Implication for AAAI_2:

- ACCS must make the conformal calibration contract explicit.
- Experiments should separate intervention quality from calibration validity.
- Include a shielding baseline without action-conditional calibration.

## Conformal Safety Priors

Conformal Safety Shielding and Conformal Predictive Safety Filters establish that conformal prediction can be used for runtime safety filters. They do not appear to solve offline safe RL under moving deployment budgets, but reviewers will expect them in related work.

Positioning:

```text
Prior conformal safety filters calibrate uncertainty for runtime safety.
ACCS calibrates offline-policy action candidates under deployment-requested budgets,
with group-conditional diagnostics and abstention as part of the reported safety evidence.
```

## Benchmark and Code Base

Primary benchmark stack:

1. DSRL / OSRL for offline safe RL datasets and baselines.
2. Safety-Gymnasium / SafePO for environment-level checks and broader safe RL context.
3. CAPS code for the direct competitor and protocol.
4. TREBI code for real-time budget-conditioned behavior.
5. FISOR code for diffusion/feasibility guidance if needed.

Initial baseline set:

```text
No shield
Global conformal shield
State-only conformal shield
Action-conditional ACCS
CAPS
CAPS + ACCS
TREBI or budget-conditioned policy baseline
OSRL baselines: BC-Safe, BC-Frontier, BCQ-Lag, BEAR-Lag, CPQ, COptiDICE, CDT
```

## Novelty Risk

Unsafe claims:

- "First to handle varying deployment constraints in offline safe RL."
- "First wrapper for offline safe RL under changing budgets."
- "Guarantees trajectory safety under arbitrary budgets."
- "Solves distribution shift."
- "First conformal method for offline safe RL."
- "Existing methods do not identify feasible actions."

Safer claims:

- "We study calibration after deployment-time action selection in offline safe RL."
- "We audit learned action-feasibility scores for false certification among issued claims."
- "We show fixed-budget evidence can fail under moving constraints, even when expected-cost metrics look acceptable."
- "We evaluate false certification among issued claims, claim yield, risk-coverage, utility at controlled risk, fallback cost, and horizon-level audit jointly."

## Required Full-PDF Reading

Before implementing broad benchmarks, read and annotate:

1. CAPS: method, proof assumptions, 38-task DSRL protocol, code entry points.
2. SafeFQL: conformal calibration of learned safety boundary, action selection, benchmark scope.
3. AEGIS: feasibility critics, any-budget claim, diffusion policy assumptions.
4. BCRL: budget-conditioned reachability definitions and guarantees.
5. Robust Probabilistic Shielding: shielding contract and offline-data assumptions.
6. CAP / selective conformal: post-selection and FCR control.
7. Conformal risk control: false certification risk as the target.
8. Off-policy conformal: policy-specific target mismatch.
9. DSRL / OSRL: dataset splits, baseline scripts, reporting format.

## Decision

Proceed with AAAI_2 only under the revised thesis:

```text
ACCS is not primarily a stronger constraint-adaptive policy optimizer.
It must be a selection-aware deployment auditor that can wrap offline safe RL policies,
including strong competitors, and control or diagnose false certification among issued claims.
```
