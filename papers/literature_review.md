# Phase 0 Literature Review

> Last updated: 2026-06-23  
> Purpose: decide whether AAAI_2 has enough novelty for an oral-ambition submission before broad experiments.

## Executive Verdict

The naive claim is already taken:

```text
Offline safe RL under changing deployment constraints without retraining.
```

CAPS is the direct prior and must be treated as the first competitor, not background. TREBI, AEGIS, and BCRL also occupy parts of the moving-budget / any-budget safety space.

The viable AAAI_2 novelty boundary is narrower but still strong:

```text
ACCS is a post-hoc deployment-evidence layer: it issues calibrated,
action-level safety claims with provenance, exposes unsupported actions,
and abstains when evidence is insufficient.
It does not claim to learn the best constraint-adaptive policy.
```

This framing can still be high-ceiling because it changes the evaluation question:

```text
not "which policy gets high return under a budget?"
but "which deployment-time action claims can be issued with finite-sample evidence?"
```

## Direct Competitors

### CAPS: critical threat and primary baseline

CAPS targets the same high-level pain point: deployment constraints can vary after offline training. It learns multiple policies with shared representation and switches at test time among policies that satisfy the current cost constraint.

Implication for AAAI_2:

- Do not sell "constraint-adaptive without retraining" as the main novelty.
- Use CAPS as the strongest baseline and probably as a base policy family.
- The ACCS difference must be: action-level calibrated claim provenance, abstention, and post-hoc evidence, not policy switching.

Required experiments:

- ACCS wrapping one fixed policy vs CAPS.
- ACCS wrapping CAPS outputs, if integration is feasible.
- CAPS vs CAPS+ACCS on claim yield, claim miscoverage, certified utility, and abstention, not only reward/cost.

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

Safer claims:

- "We reframe deployment-time safety as a calibrated action-level evidence problem."
- "We provide a post-hoc conformal action-safety claim protocol with provenance and abstention under insufficient calibration evidence."
- "We show fixed-budget evidence can fail under moving constraints, even when expected-cost metrics look acceptable."
- "We evaluate certified utility, claim yield, claim miscoverage, unsupported safety success, adaptivity, and horizon-level audit jointly."

## Required Full-PDF Reading

Before implementing broad benchmarks, read and annotate:

1. CAPS: method, proof assumptions, 38-task DSRL protocol, code entry points.
2. AEGIS: feasibility critics, any-budget claim, diffusion policy assumptions.
3. BCRL: budget-conditioned reachability definitions and guarantees.
4. Robust Probabilistic Shielding: shielding contract and offline-data assumptions.
5. Conformal Safety Shielding: exact conformal guarantee and limitation.
6. DSRL / OSRL: dataset splits, baseline scripts, reporting format.

## Decision

Proceed with AAAI_2 only under the revised thesis:

```text
ACCS is not primarily a stronger constraint-adaptive policy optimizer.
It is a deployment-time safety claim protocol that can wrap offline safe RL policies,
including strong competitors, and issue calibrated action-level claims or abstain.
```
