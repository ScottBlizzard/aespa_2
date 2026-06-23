# Literature Threat Map

> Last updated: 2026-06-23

## Top-Level Verdict

AAAI_2 remains viable only after narrowing the claim.

Rejected broad novelty:

```text
Handling moving deployment constraints in offline safe RL.
```

Accepted novelty target:

```text
Post-hoc action-conditional conformal safety claims with provenance for offline safe RL under moving deployment constraints.
```

## Threat Levels

| Work | Threat | Why it matters | Required response |
|---|---:|---|---|
| CAPS | Critical | Same moving-constraint OSRL setting, public code, AAAI 2025 oral-level signal. | Make primary baseline; distinguish evidence layer from policy switching. |
| AEGIS | Critical | Claims almost-sure safety for any feasible budget. | Avoid arbitrary-budget guarantee claims; compare if code exists. |
| BCRL | High | Budget-conditioned reachability is a principled any-budget formulation. | Contrast reachability sets with calibrated action reports. |
| Robust Probabilistic Shielding | High | Runtime shielding for offline safe RL. | Show ACCS calibration/abstention contract is different. |
| TREBI | High | Real-time budget constraints. | Use as budget-conditioned baseline or conceptual prior. |
| Conformal Safety Shielding | Medium-High | Conformal runtime shielding prior. | Cite and separate from offline safe RL moving-budget evaluation. |
| DSRL / OSRL | Critical infrastructure | Main benchmark and baseline ecosystem. | Reuse, do not reinvent. |

## Paper Position After Gate

The paper should open with:

```text
Existing offline safe RL methods can adapt or optimize for cost budgets,
but deployment still lacks action-level claim provenance about which proposed
actions are justified under the requested constraint and calibration data.
```

Then define ACCS as:

```text
a budget-uniform certificate protocol that turns an offline policy proposal
into an action-safety claim: execute, replace, or abstain,
with finite-sample calibration provenance.
```

## Minimum Baseline Set

For a credible AAAI submission:

1. No shield.
2. Global conformal shield.
3. State-only conformal shield.
4. ACCS.
5. CAPS.
6. CAPS + ACCS.
7. One budget-conditioned baseline: TREBI or BCRL-style proxy.
8. Standard OSRL baselines from OSRL/DSRL.

## Reviewer Attack Surface

Likely attacks:

- "CAPS already solves changing constraints."
- "Conformal safety shielding already exists."
- "Action-level coverage is weaker than trajectory safety."
- "Abstention makes the method conservative."
- "Calibration split is unrealistic under deployment shift."

Required defenses:

- Show CAPS optimizes/switches policies, while ACCS reports calibrated action evidence.
- Show CAPS+ACCS improves claim provenance over CAPS alone.
- Show global conformal is safe but too coarse; action-conditional calibration improves certified utility at matched claim miscoverage.
- Report horizon-level violation separately and honestly.
- Make abstention a measured output, not an implementation detail.
- Include shift audits and state what is not guaranteed.
