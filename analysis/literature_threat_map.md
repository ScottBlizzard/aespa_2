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
Selection-aware finite-data auditing for false certification among deployment-time action claims in offline safe RL.
```

## Threat Levels

| Work | Threat | Why it matters | Required response |
|---|---:|---|---|
| CAPS | Critical | Same moving-constraint OSRL setting, public code, AAAI 2025 oral-level signal. | Make primary baseline; distinguish evidence layer from policy switching. |
| SafeFQL | Critical | Offline safe RL with reachability-style safe action selection and conformal calibration of a learned safety boundary. | Add immediately; claim novelty only in selection-aware false-certification control. |
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
and several already identify feasible actions. The remaining gap is finite-data
calibration after deployment-time action selection: selected actions can
concentrate score errors even when marginal calibration looks valid.
```

Then define ACCS as:

```text
a selection-aware auditor that wraps learned action-feasibility scores,
controls or diagnoses false certification among issued action claims,
and abstains when overlap or calibration support is insufficient.
```

## Minimum Baseline Set

For a credible AAAI submission:

1. No shield.
2. Global conformal shield.
3. State-only conformal shield.
4. Group/Mondrian conformal shield.
5. Conformal risk control / selective conformal baseline.
6. Selection-aware ACCS.
7. CAPS.
8. CAPS + global CP.
9. CAPS + group CP.
10. CAPS + selection-aware ACCS.
11. SafeFQL.
12. One budget-conditioned baseline: TREBI or BCRL-style proxy.
13. Standard OSRL baselines from OSRL/DSRL.

## Reviewer Attack Surface

Likely attacks:

- "CAPS already solves changing constraints."
- "SafeFQL already combines conformal calibration and offline safe RL."
- "Conformal safety shielding already exists."
- "Accepted-action theorem confuses marginal coverage with selected-claim risk."
- "Residual-cost labels are policy-specific and not observed offline."
- "Action-level coverage is weaker than trajectory safety."
- "Abstention makes the method conservative."
- "Calibration split is unrealistic under deployment shift."

Required defenses:

- Explicitly concede CAPS/AEGIS/BCRL/SafeFQL action-feasibility prior work.
- Show ordinary global/group conformal fails after selection in an exact toy.
- Show selection-aware ACCS controls false certification among issued claims.
- Show CAPS+selection-aware ACCS improves auditing over CAPS+global/group conformal.
- Report horizon-level violation separately and honestly.
- Make abstention a measured output, not an implementation detail.
- Include shift audits and state what is not guaranteed.
