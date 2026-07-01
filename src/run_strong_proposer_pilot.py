"""First non-toy strong-proposer pilot.

This script implements the staged pilot in
``analysis/strong_proposer_protocol.md``.  It builds a synthetic
OSRL-style query bank with continuous states/actions, simulator-branch
residual labels, and a fixed set of auditors evaluated on the same
candidate bank.

The goal is not to claim benchmark performance.  The goal is to validate
the paper-facing experimental contract before integrating CAPS/SafeFQL.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"

PROTOCOL_VERSION = "2026-06-23"
ENV_ID = "SyntheticHazardNavigation-v0"
PROPOSER_NAME = "synthetic_osrl_mixture_v1"

HAZARD_CENTERS = np.array([[0.02, -0.24], [0.05, 0.28]], dtype=float)
HAZARD_RADIUS = 0.23
HAZARD_TEMP = 0.045


@dataclass(frozen=True)
class PilotConfig:
    seed: int = 20260623
    k: int = 16
    n_train: int = 4000
    n_tune: int = 4000
    n_audit: int = 9000
    n_test: int = 25000
    branches: int = 8
    horizon: int = 18
    alpha: float = 0.05
    gamma: float = 0.55
    delta: float = 0.05
    violation_prob_threshold: float = 0.125
    save_query_bank: bool = True


@dataclass(frozen=True)
class SplitBank:
    state: np.ndarray
    budget: np.ndarray
    candidate_actions: np.ndarray
    reward_scores: np.ndarray
    safety_scores: np.ndarray
    support_scores: np.ndarray
    residual_risk: np.ndarray
    residual_failure: np.ndarray
    fallback_index: np.ndarray


@dataclass(frozen=True)
class AuditorResult:
    name: str
    selected_false_certification: float
    claim_yield: float
    normalized_reward: float
    fallback_rate: float
    support_rejection_rate: float
    episode_violation_rate: float
    issued: int
    failures: int
    selected_rule: Optional[Dict[str, float]]


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def clip_norm(x: np.ndarray, max_norm: float) -> np.ndarray:
    norm = np.linalg.norm(x, axis=-1, keepdims=True)
    scale = np.minimum(1.0, max_norm / np.maximum(norm, 1e-9))
    return x * scale


def unit(x: np.ndarray) -> np.ndarray:
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-9)


def sample_states(rng: np.random.Generator, n: int) -> Tuple[np.ndarray, np.ndarray]:
    """Sample continuous navigation states and residual safety budgets."""

    pos = np.column_stack(
        [
            rng.normal(-0.78, 0.10, size=n),
            rng.uniform(-0.48, 0.48, size=n),
        ]
    )
    goal = np.column_stack(
        [
            rng.normal(0.93, 0.05, size=n),
            rng.uniform(-0.42, 0.42, size=n),
        ]
    )
    pos[:, 0] = np.clip(pos[:, 0], -0.96, -0.50)
    pos[:, 1] = np.clip(pos[:, 1], -0.55, 0.55)
    goal[:, 0] = np.clip(goal[:, 0], 0.75, 1.05)
    state = np.column_stack([pos, goal])
    budget = rng.uniform(0.68, 0.98, size=n)
    return state, budget


def hazard_repulsion(pos: np.ndarray) -> np.ndarray:
    """Repulsive field used by the declared continuation/fallback policy."""

    diff = pos[:, None, :] - HAZARD_CENTERS[None, :, :]
    dist = np.maximum(np.linalg.norm(diff, axis=-1, keepdims=True), 1e-6)
    weight = np.exp(-((dist[..., 0] / 0.38) ** 2))[..., None]
    repulsion = (diff / dist * weight).sum(axis=1)
    return repulsion


def behavior_mean_action(state: np.ndarray) -> np.ndarray:
    pos = state[:, :2]
    goal = state[:, 2:4]
    direct = unit(goal - pos)
    perp = np.column_stack([-direct[:, 1], direct[:, 0]])
    side = np.where(pos[:, 1] >= 0.0, 1.0, -1.0)[:, None]
    corridor = side * perp
    repel = hazard_repulsion(pos)
    mean = unit(0.58 * direct + 0.86 * corridor + 0.32 * unit(repel)) * 0.22
    return mean


def segment_hazard_distance(pos: np.ndarray, action: np.ndarray) -> np.ndarray:
    """Minimum distance from the one-step segment to any hazard center."""

    if action.ndim == 2:
        pos2 = pos
        action2 = action
    else:
        pos2 = np.repeat(pos[:, None, :], action.shape[1], axis=1)
        action2 = action
    start = pos2[..., None, :]
    step = action2[..., None, :]
    centers = HAZARD_CENTERS.reshape((1,) * (start.ndim - 2) + HAZARD_CENTERS.shape)
    denom = np.maximum((step * step).sum(axis=-1, keepdims=True), 1e-9)
    t = np.clip(((centers - start) * step).sum(axis=-1, keepdims=True) / denom, 0.0, 1.0)
    closest = start + t * step
    dist = np.linalg.norm(closest - centers, axis=-1)
    return dist.min(axis=-1)


def hazard_exposure(pos: np.ndarray) -> np.ndarray:
    dist = np.linalg.norm(pos[:, None, :] - HAZARD_CENTERS[None, :, :], axis=-1).min(axis=1)
    soft = sigmoid((HAZARD_RADIUS - dist) / HAZARD_TEMP)
    hard = (dist < HAZARD_RADIUS * 0.70).astype(float)
    return 0.035 * soft + 0.16 * hard


def generate_candidate_actions(
    rng: np.random.Generator,
    state: np.ndarray,
    k: int,
) -> np.ndarray:
    """Mixture proposer with supported actions and high-reward shortcuts."""

    n = state.shape[0]
    pos = state[:, :2]
    goal = state[:, 2:4]
    direct = unit(goal - pos)
    mean = behavior_mean_action(state)
    perp = np.column_stack([-direct[:, 1], direct[:, 0]])
    side = np.where(pos[:, 1] >= 0.0, 1.0, -1.0)[:, None]
    detour_dir = unit(0.62 * direct + 0.92 * side * perp)

    modes = rng.choice(3, size=(n, k), p=[0.52, 0.30, 0.18])
    actions = np.empty((n, k, 2), dtype=float)

    supported = mean[:, None, :] + rng.normal(0.0, 0.045, size=(n, k, 2))
    shortcut_speed = rng.normal(0.39, 0.045, size=(n, k, 1))
    shortcut = direct[:, None, :] * shortcut_speed + rng.normal(0.0, 0.035, size=(n, k, 2))
    detour_speed = rng.normal(0.25, 0.030, size=(n, k, 1))
    detour = detour_dir[:, None, :] * detour_speed + rng.normal(0.0, 0.035, size=(n, k, 2))

    actions[modes == 0] = supported[modes == 0]
    actions[modes == 1] = shortcut[modes == 1]
    actions[modes == 2] = detour[modes == 2]
    return clip_norm(actions, 0.45)


def score_candidates(
    rng: np.random.Generator,
    state: np.ndarray,
    budget: np.ndarray,
    actions: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return reward, model safety score, and behavior support score."""

    pos = state[:, :2]
    goal = state[:, 2:4]
    mean = behavior_mean_action(state)
    next_pos = pos[:, None, :] + actions
    before = np.linalg.norm(goal - pos, axis=1)[:, None]
    after = np.linalg.norm(goal[:, None, :] - next_pos, axis=-1)
    progress = before - after
    speed = np.linalg.norm(actions, axis=-1)
    seg_dist = segment_hazard_distance(pos, actions)
    seg_exposure = sigmoid((HAZARD_RADIUS + 0.02 - seg_dist) / HAZARD_TEMP)

    support_dist = np.linalg.norm(actions - mean[:, None, :], axis=-1)
    support = np.exp(-0.5 * (support_dist / 0.115) ** 2)
    support *= np.exp(-1.5 * np.maximum(speed - 0.31, 0.0) ** 2 / 0.05**2)
    support = np.clip(support, 0.0, 1.0)

    reward_raw = 2.8 * progress + 0.40 * speed - 0.16 * seg_exposure
    reward_raw += rng.normal(0.0, 0.025, size=reward_raw.shape)
    reward = sigmoid(4.2 * reward_raw + 0.35)

    budget_pressure = np.clip((0.46 - budget[:, None]) / 0.18, -0.5, 1.2)
    speed_excess = np.maximum(speed - 0.28, 0.0)
    model_risk = 0.50 * seg_exposure + 0.45 * speed_excess + 0.16 * budget_pressure
    # The deliberate proposer weakness: off-support shortcuts are over-trusted.
    model_risk -= 0.42 * (1.0 - support)
    model_risk += rng.normal(0.0, 0.045, size=model_risk.shape)
    safety_score = np.clip(sigmoid(2.1 * model_risk - 1.0), 0.0, 1.0)
    return reward, safety_score, support


def branch_residual_risk(
    rng: np.random.Generator,
    state: np.ndarray,
    budget: np.ndarray,
    actions: np.ndarray,
    branches: int,
    horizon: int,
) -> np.ndarray:
    """Simulator-assisted residual labels after first action."""

    n, k, _ = actions.shape
    total = n * k * branches
    pos = np.repeat(np.repeat(state[:, None, :2], k, axis=1).reshape(-1, 2), branches, axis=0)
    goal = np.repeat(np.repeat(state[:, None, 2:4], k, axis=1).reshape(-1, 2), branches, axis=0)
    budget_flat = np.repeat(np.repeat(budget[:, None], k, axis=1).reshape(-1), branches)
    first = np.repeat(actions.reshape(-1, 2), branches, axis=0)

    pos = pos + first + rng.normal(0.0, 0.025, size=(total, 2))
    cost = hazard_exposure(pos)
    min_dist = np.linalg.norm(pos[:, None, :] - HAZARD_CENTERS[None, :, :], axis=-1).min(axis=1)

    for _ in range(horizon):
        direct = unit(goal - pos)
        perp = np.column_stack([-direct[:, 1], direct[:, 0]])
        side = np.where(pos[:, 1] >= 0.0, 1.0, -1.0)[:, None]
        corridor = side * perp
        repel = hazard_repulsion(pos)
        action = unit(0.68 * direct + 0.74 * corridor + 0.44 * unit(repel)) * 0.18
        action += rng.normal(0.0, 0.030, size=action.shape)
        action = clip_norm(action, 0.24)
        pos = pos + action + rng.normal(0.0, 0.018, size=pos.shape)
        cost += hazard_exposure(pos)
        step_dist = np.linalg.norm(pos[:, None, :] - HAZARD_CENTERS[None, :, :], axis=-1).min(axis=1)
        min_dist = np.minimum(min_dist, step_dist)

    collision = min_dist < HAZARD_RADIUS * 0.62
    violation = (cost > budget_flat) | collision
    return violation.reshape(n, k, branches).mean(axis=2)


def build_split(
    rng: np.random.Generator,
    n: int,
    k: int,
    branches: int,
    horizon: int,
    violation_prob_threshold: float,
) -> SplitBank:
    state, budget = sample_states(rng, n)
    actions = generate_candidate_actions(rng, state, k)
    reward, safety, support = score_candidates(rng, state, budget, actions)
    residual_risk = branch_residual_risk(rng, state, budget, actions, branches, horizon)
    failure = residual_risk > violation_prob_threshold
    fallback_index = choose_fallback_index(reward, safety, support)
    return SplitBank(
        state=state,
        budget=budget,
        candidate_actions=actions,
        reward_scores=reward,
        safety_scores=safety,
        support_scores=support,
        residual_risk=residual_risk,
        residual_failure=failure,
        fallback_index=fallback_index,
    )


def choose_fallback_index(reward: np.ndarray, safety: np.ndarray, support: np.ndarray) -> np.ndarray:
    eligible = (support >= 0.45) & (safety <= 0.55)
    score = np.where(eligible, reward + 0.15 * support - 0.10 * safety, -np.inf)
    missing = ~np.isfinite(score).any(axis=1)
    if missing.any():
        score[missing] = support[missing] - 0.20 * safety[missing]
    return np.argmax(score, axis=1)


def one_sided_ucb(failures: int, n: int, n_rules: int, delta: float) -> float:
    if n <= 0:
        return float("inf")
    eps = np.sqrt(np.log(2.0 * max(n_rules, 1) / delta) / (2.0 * n))
    return float(min(1.0, failures / n + eps))


def yield_lcb(issued: int, n_blocks: int, n_rules: int, delta: float) -> float:
    eps = np.sqrt(np.log(2.0 * max(n_rules, 1) / delta) / (2.0 * n_blocks))
    return float(max(0.0, issued / n_blocks - eps))


def select_best_by_reward(reward: np.ndarray, eligible: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    issued = eligible.any(axis=1)
    masked = np.where(eligible, reward, -np.inf)
    selected = np.argmax(masked, axis=1)
    selected[~issued] = -1
    return issued, selected


def evaluate_eligible(
    bank: SplitBank,
    eligible: np.ndarray,
    name: str,
    selected_rule: Optional[Dict[str, float]] = None,
) -> AuditorResult:
    reward = bank.reward_scores
    failure = bank.residual_failure
    support = bank.support_scores
    issued, selected = select_best_by_reward(reward, eligible)
    rows = np.arange(reward.shape[0])
    top_original = reward.argmax(axis=1)
    fallback = bank.fallback_index

    selected_or_fallback = np.where(issued, selected, fallback)
    selected_reward = reward[rows, selected_or_fallback]
    selected_failure = failure[rows, selected_or_fallback]
    false_when_issued = np.zeros_like(issued, dtype=bool)
    false_when_issued[issued] = failure[rows[issued], selected[issued]]
    support_rejected = selected_or_fallback != top_original

    issued_count = int(issued.sum())
    failures = int(false_when_issued.sum())
    risk = failures / issued_count if issued_count else 0.0
    return AuditorResult(
        name=name,
        selected_false_certification=float(risk),
        claim_yield=float(issued.mean()),
        normalized_reward=float(selected_reward.mean()),
        fallback_rate=float((~issued).mean()),
        support_rejection_rate=float(support_rejected.mean()),
        episode_violation_rate=float(selected_failure.mean()),
        issued=issued_count,
        failures=failures,
        selected_rule=selected_rule,
    )


def fit_candidate_threshold(
    audit: SplitBank,
    alpha: float,
    delta: float,
    thresholds: np.ndarray,
) -> Optional[float]:
    candidates = []
    safety = audit.safety_scores
    failure = audit.residual_failure
    reward = audit.reward_scores
    for tau in thresholds:
        mask = safety <= tau
        n = int(mask.sum())
        f = int((failure & mask).sum())
        risk_ucb = one_sided_ucb(f, n, len(thresholds), delta)
        if risk_ucb <= alpha:
            candidates.append((float(reward[mask].mean()) if n else -np.inf, float(tau), risk_ucb, n))
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1]))[1]


def fit_reward_bin_certifier(
    audit: SplitBank,
    n_bins: int,
    alpha: float,
    delta: float,
) -> Dict[str, np.ndarray]:
    reward = audit.reward_scores.reshape(-1)
    failure = audit.residual_failure.reshape(-1)
    edges = np.quantile(reward, np.linspace(0.0, 1.0, n_bins + 1))
    edges[0] = -np.inf
    edges[-1] = np.inf
    bin_id = np.clip(np.searchsorted(edges, reward, side="right") - 1, 0, n_bins - 1)
    certified = np.zeros(n_bins, dtype=bool)
    risk_ucb = np.full(n_bins, np.inf)
    for idx in range(n_bins):
        mask = bin_id == idx
        risk_ucb[idx] = one_sided_ucb(int(failure[mask].sum()), int(mask.sum()), n_bins, delta)
        certified[idx] = risk_ucb[idx] <= alpha
    return {"edges": edges, "certified": certified, "risk_ucb": risk_ucb}


def evaluate_reward_bin(bank: SplitBank, certifier: Dict[str, np.ndarray]) -> np.ndarray:
    edges = certifier["edges"]
    certified = certifier["certified"]
    bin_id = np.clip(np.searchsorted(edges, bank.reward_scores, side="right") - 1, 0, len(certified) - 1)
    return certified[bin_id]


def fit_rank_certifier(audit: SplitBank, alpha: float, delta: float) -> np.ndarray:
    order = np.argsort(-audit.reward_scores, axis=1)
    ranked_failure = np.take_along_axis(audit.residual_failure, order, axis=1)
    n_rules = ranked_failure.shape[1]
    certified = np.zeros(n_rules, dtype=bool)
    for rank in range(n_rules):
        certified[rank] = (
            one_sided_ucb(int(ranked_failure[:, rank].sum()), ranked_failure.shape[0], n_rules, delta)
            <= alpha
        )
    return certified


def evaluate_rank(bank: SplitBank, certified_rank: np.ndarray) -> np.ndarray:
    order = np.argsort(-bank.reward_scores, axis=1)
    eligible_ranked = np.repeat(certified_rank[None, :], bank.reward_scores.shape[0], axis=0)
    eligible = np.zeros_like(eligible_ranked, dtype=bool)
    np.put_along_axis(eligible, order, eligible_ranked, axis=1)
    return eligible


def threshold_grid(x: np.ndarray, n_grid: int, low: float = 0.02, high: float = 0.98) -> np.ndarray:
    return np.unique(np.quantile(x.reshape(-1), np.linspace(low, high, n_grid)))


def fit_selected_rule_family(
    audit: SplitBank,
    rules: Iterable[Tuple[float, float]],
    alpha: float,
    gamma: float,
    delta: float,
    use_support: bool,
) -> Optional[Dict[str, float]]:
    rules = list(rules)
    candidates: List[Dict[str, float]] = []
    n_rules = len(rules)
    for safety_tau, support_tau in rules:
        eligible = audit.safety_scores <= safety_tau
        if use_support:
            eligible &= audit.support_scores >= support_tau
        evaluated = evaluate_eligible(audit, eligible, name="audit")
        risk_ucb = one_sided_ucb(evaluated.failures, evaluated.issued, n_rules, delta)
        ylcb = yield_lcb(evaluated.issued, audit.reward_scores.shape[0], n_rules, delta)
        feasible = risk_ucb <= alpha and ylcb >= gamma
        if feasible:
            candidates.append(
                {
                    "safety_tau": float(safety_tau),
                    "support_tau": float(support_tau),
                    "audit_risk_ucb": float(risk_ucb),
                    "audit_yield_lcb": float(ylcb),
                    "audit_reward": float(evaluated.normalized_reward),
                    "audit_yield": float(evaluated.claim_yield),
                }
            )
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item["audit_reward"], item["audit_yield"]))


def build_auditors(audit: SplitBank, test: SplitBank, cfg: PilotConfig) -> List[AuditorResult]:
    results: List[AuditorResult] = []
    n, k = test.reward_scores.shape

    results.append(
        evaluate_eligible(test, np.ones((n, k), dtype=bool), "none_original_proposer")
    )

    safety_thresholds = threshold_grid(audit.safety_scores, 80)
    tau = fit_candidate_threshold(audit, cfg.alpha, cfg.delta, safety_thresholds)
    if tau is None:
        eligible = np.zeros((n, k), dtype=bool)
        rule = None
    else:
        eligible = test.safety_scores <= tau
        rule = {"safety_tau": float(tau)}
    results.append(evaluate_eligible(test, eligible, "global_candidate_cp", rule))

    reward_cert = fit_reward_bin_certifier(audit, n_bins=20, alpha=cfg.alpha, delta=cfg.delta)
    results.append(
        evaluate_eligible(
            test,
            evaluate_reward_bin(test, reward_cert),
            "reward_bin_ucb_20",
            {
                "certified_bins": int(reward_cert["certified"].sum()),
                "max_risk_ucb": float(np.max(reward_cert["risk_ucb"][reward_cert["certified"]]))
                if reward_cert["certified"].any()
                else float("nan"),
            },
        )
    )

    rank_cert = fit_rank_certifier(audit, cfg.alpha, cfg.delta)
    results.append(
        evaluate_eligible(
            test,
            evaluate_rank(test, rank_cert),
            "rank_bin_ucb",
            {
                "certified_ranks": int(rank_cert.sum()),
                "first_certified_rank": int(np.flatnonzero(rank_cert)[0] + 1)
                if rank_cert.any()
                else -1,
            },
        )
    )

    safety_rules = [(float(x), 0.0) for x in safety_thresholds]
    crc_rule = fit_selected_rule_family(
        audit,
        safety_rules,
        alpha=cfg.alpha,
        gamma=cfg.gamma,
        delta=cfg.delta,
        use_support=False,
    )
    if crc_rule is None:
        eligible = np.zeros((n, k), dtype=bool)
    else:
        eligible = test.safety_scores <= crc_rule["safety_tau"]
    results.append(evaluate_eligible(test, eligible, "crc_style_safety_threshold", crc_rule))

    support_thresholds = np.unique(
        np.concatenate([[0.0], np.quantile(audit.support_scores.reshape(-1), np.linspace(0.10, 0.85, 16))])
    )
    accs_rules = [(float(st), float(su)) for st in safety_thresholds[::2] for su in support_thresholds]
    accs_rule = fit_selected_rule_family(
        audit,
        accs_rules,
        alpha=cfg.alpha,
        gamma=cfg.gamma,
        delta=cfg.delta,
        use_support=True,
    )
    if accs_rule is None:
        eligible = np.zeros((n, k), dtype=bool)
    else:
        eligible = (test.safety_scores <= accs_rule["safety_tau"]) & (
            test.support_scores >= accs_rule["support_tau"]
        )
    results.append(evaluate_eligible(test, eligible, "accs_v0_support_safety", accs_rule))

    oracle = test.residual_risk <= cfg.violation_prob_threshold
    results.append(evaluate_eligible(test, oracle, "oracle_residual_label", None))
    return results


def save_query_bank(path: Path, audit: SplitBank, test: SplitBank) -> None:
    np.savez_compressed(
        path,
        audit_state=audit.state,
        audit_budget=audit.budget,
        audit_candidate_actions=audit.candidate_actions,
        audit_reward_scores=audit.reward_scores,
        audit_safety_scores=audit.safety_scores,
        audit_support_scores=audit.support_scores,
        audit_residual_risk=audit.residual_risk,
        audit_residual_failure=audit.residual_failure,
        test_state=test.state,
        test_budget=test.budget,
        test_candidate_actions=test.candidate_actions,
        test_reward_scores=test.reward_scores,
        test_safety_scores=test.safety_scores,
        test_support_scores=test.support_scores,
        test_residual_risk=test.residual_risk,
        test_residual_failure=test.residual_failure,
    )


def make_report(payload: Dict[str, object], out_md: Path) -> None:
    rows = payload["auditors"]
    df = pd.DataFrame(rows)
    cols = [
        "name",
        "selected_false_certification",
        "claim_yield",
        "normalized_reward",
        "fallback_rate",
        "support_rejection_rate",
        "episode_violation_rate",
    ]
    table_rows = []
    table_rows.append("| " + " | ".join(cols) + " |")
    table_rows.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for row in df[cols].to_dict(orient="records"):
        values = []
        for col in cols:
            value = row[col]
            if isinstance(value, float):
                values.append(f"{value:.4f}")
            else:
                values.append(str(value))
        table_rows.append("| " + " | ".join(values) + " |")
    table = "\n".join(table_rows)
    best = df[df["name"] == "accs_v0_support_safety"].iloc[0].to_dict()
    text = f"""# Strong Proposer Pilot Server Report

Protocol version: `{payload["protocol_version"]}`

Proposer: `{payload["proposer"]}`

Environment: `{payload["env"]}`

Residual label protocol: `{payload["residual_label_protocol"]}`

## Main Metrics

{table}

## ACCS-v0 Selected Rule

```json
{json.dumps(best["selected_rule"], indent=2)}
```

## Interpretation

This is a synthetic OSRL-style pilot, not yet a benchmark result.  Its
purpose is to validate the query-bank, residual-label, and auditor
comparison pipeline before CAPS/SafeFQL integration.
"""
    out_md.write_text(text, encoding="utf-8")


def run_pilot(cfg: PilotConfig, out_json: Path, out_md: Path) -> Dict[str, object]:
    rng = np.random.default_rng(cfg.seed)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Train/tune are generated to freeze split semantics, but this pilot has
    # no learned proposer.  Audit/test are the only splits used by auditors.
    train_state, _ = sample_states(rng, cfg.n_train)
    tune_state, _ = sample_states(rng, cfg.n_tune)
    audit = build_split(
        rng,
        cfg.n_audit,
        cfg.k,
        cfg.branches,
        cfg.horizon,
        cfg.violation_prob_threshold,
    )
    test = build_split(
        rng,
        cfg.n_test,
        cfg.k,
        cfg.branches,
        cfg.horizon,
        cfg.violation_prob_threshold,
    )
    auditors = build_auditors(audit, test, cfg)

    query_bank_file = OUTPUT_DIR / "phase_strong_proposer_query_bank_server.npz"
    if cfg.save_query_bank:
        save_query_bank(query_bank_file, audit, test)

    payload: Dict[str, object] = {
        "protocol_version": PROTOCOL_VERSION,
        "proposer": PROPOSER_NAME,
        "env": ENV_ID,
        "splits": {
            "train": int(train_state.shape[0]),
            "tune": int(tune_state.shape[0]),
            "audit": cfg.n_audit,
            "test": cfg.n_test,
        },
        "query_bank": {
            "schema": "analysis/strong_proposer_protocol.md::QueryBlock",
            "file": str(query_bank_file.relative_to(ROOT)) if cfg.save_query_bank else None,
            "n_audit_blocks": cfg.n_audit,
            "n_test_blocks": cfg.n_test,
            "k": cfg.k,
            "state_dim": 4,
            "action_dim": 2,
            "proposer_name": PROPOSER_NAME,
            "proposer_checkpoint": "procedural_seed_%d" % cfg.seed,
            "continuation_policy": "hazard_repulsive_goal_policy",
            "fallback_policy": "support_high_safety_low_behavior_policy",
            "seed": cfg.seed,
        },
        "residual_label_protocol": (
            "simulator branching: execute candidate action, continue with declared "
            f"hazard-repulsive policy for H={cfg.horizon}, M={cfg.branches} branches; "
            f"false label if branch violation rate > {cfg.violation_prob_threshold}"
        ),
        "config": asdict(cfg),
        "auditors": [asdict(result) for result in auditors],
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    make_report(payload, out_md)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=PilotConfig.seed)
    parser.add_argument("--k", type=int, default=PilotConfig.k)
    parser.add_argument("--n-train", type=int, default=PilotConfig.n_train)
    parser.add_argument("--n-tune", type=int, default=PilotConfig.n_tune)
    parser.add_argument("--n-audit", type=int, default=PilotConfig.n_audit)
    parser.add_argument("--n-test", type=int, default=PilotConfig.n_test)
    parser.add_argument("--branches", type=int, default=PilotConfig.branches)
    parser.add_argument("--horizon", type=int, default=PilotConfig.horizon)
    parser.add_argument("--alpha", type=float, default=PilotConfig.alpha)
    parser.add_argument("--gamma", type=float, default=PilotConfig.gamma)
    parser.add_argument("--delta", type=float, default=PilotConfig.delta)
    parser.add_argument(
        "--violation-prob-threshold",
        type=float,
        default=PilotConfig.violation_prob_threshold,
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=OUTPUT_DIR / "phase_strong_proposer_pilot_server.json",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=OUTPUT_DIR / "phase_strong_proposer_pilot_server.md",
    )
    parser.add_argument("--no-query-bank", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = PilotConfig(
        seed=args.seed,
        k=args.k,
        n_train=args.n_train,
        n_tune=args.n_tune,
        n_audit=args.n_audit,
        n_test=args.n_test,
        branches=args.branches,
        horizon=args.horizon,
        alpha=args.alpha,
        gamma=args.gamma,
        delta=args.delta,
        violation_prob_threshold=args.violation_prob_threshold,
        save_query_bank=not args.no_query_bank,
    )
    payload = run_pilot(cfg, args.out_json, args.out_md)
    df = pd.DataFrame(payload["auditors"])
    print(
        df[
            [
                "name",
                "selected_false_certification",
                "claim_yield",
                "normalized_reward",
                "fallback_rate",
                "support_rejection_rate",
                "episode_violation_rate",
            ]
        ].to_string(index=False)
    )
    print(f"Wrote {args.out_json}")
    print(f"Wrote {args.out_md}")


if __name__ == "__main__":
    main()
