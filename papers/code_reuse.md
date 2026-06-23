# Code Reuse Plan

> Last updated: 2026-06-23

## Priority 1: OSRL / DSRL

Use as the main local/server baseline framework.

Targets:

- dataset loading and task naming;
- baselines: BC-All, BC-Safe, BC-Frontier, BCQ-Lag, BEAR-Lag, CPQ, COptiDICE, CDT;
- evaluation protocol over multiple cost budgets;
- JSON result layout compatible with `outputs/*_server.json`.

Expected local wrapper:

```text
src/osrl_adapter.py
src/dsrl_tasks.py
src/eval_metrics.py
```

## Priority 2: CAPS

CAPS is the direct competitor. Its code follows OSRL, which should make integration realistic.

Integration target:

```text
base_policy = CAPSPolicy(...)
report = ACCS.wrap(base_policy).evaluate(dataset, requested_budget)
```

Required comparisons:

1. CAPS alone.
2. ACCS over a single fixed policy.
3. ACCS over CAPS action proposals.
4. Global conformal shield over the same base actions.

## Priority 3: TREBI

TREBI covers real-time budget constraints and has code. It is useful for:

- budget-conditioned baseline behavior;
- toy/main phenomenon design;
- sanity check that ACCS is not rediscovering budget conditioning.

## Priority 4: Safety-Gymnasium / SafePO

Use for the Phase 3 main benchmark only after the toy phenomenon is clean.

Targets:

- 2-3 environments with clear cost signals;
- offline dataset generation or reuse through DSRL/OSRL where possible;
- safety-policy baselines from SafePO as context, not necessarily all as main baselines.

## Priority 5: FISOR / AEGIS-Style Feasibility Guidance

Use only if Phase 1 and CAPS comparisons are positive. Feasibility-guided diffusion policies are high-effort and can distract from the core ACCS evidence claim.

## Common Result Schema

Every adapter should produce:

```json
{
  "project": "AAAI_2_ACCS",
  "phase": "phase_name",
  "task": "task_name",
  "seed": 0,
  "base_policy": "policy_name",
  "shield": "none|global_conformal|state_conformal|accs|competitor",
  "requested_budget": 10.0,
  "reward_mean": 0.0,
  "cost_mean": 0.0,
  "episode_violation_rate": 0.0,
  "action_miscoverage": 0.0,
  "group_miscoverage": {},
  "abstention_rate": 0.0,
  "replacement_rate": 0.0,
  "calibration_size": 0,
  "notes": ""
}
```

## Implementation Rule

Do not fork a large external repository into this project until the exact entry points are known. Keep AAAI_2 code as thin adapters around installed or cloned server-side baselines.
