"""DSRL environment pilot with a learned one-step proposer.

This is the first bridge from the synthetic query-bank pilot to an actual DSRL
environment.  It uses ``OfflineBallCircle-v0`` as a simulator, generates a
project-local offline training set, fits lightweight reward/safety scorers, and
then evaluates selection-aware certification rules on fixed audit/test query
banks.

The script is intended to run on the A40 Python 3.10 environment:

    .venv310/bin/python src/run_dsrl_env_pilot.py

It does not depend on the public DSRL HDF5 download, which is currently not
reachable from the server.
"""

from __future__ import annotations

import argparse
import json
import os
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
PROTOCOL_VERSION = "2026-06-23"
ENV_ID = "OfflineBallCircle-v0"
PROPOSER_NAME = "dsrl_ballcircle_learned_one_step_v1"


@dataclass(frozen=True)
class DSRLPilotConfig:
    seed: int = 20260624
    env_id: str = ENV_ID
    k: int = 16
    n_model: int = 6000
    n_tune: int = 500
    n_audit: int = 2500
    n_test: int = 6000
    branches: int = 3
    horizon: int = 10
    prefix_len: int = 40
    alpha: float = 0.05
    gamma: float = 0.50
    delta: float = 0.05
    risk_quantile: float = 0.965
    save_query_bank: bool = True


@dataclass(frozen=True)
class EnvBank:
    seeds: np.ndarray
    prefixes: np.ndarray
    state: np.ndarray
    candidate_actions: np.ndarray
    reward_scores: np.ndarray
    safety_scores: np.ndarray
    support_scores: np.ndarray
    residual_cost: np.ndarray
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


def make_env(env_id: str):
    warnings.filterwarnings("ignore", category=UserWarning)
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import gymnasium as gym  # type: ignore
    import dsrl  # noqa: F401  # type: ignore

    return gym.make(env_id)


def reset_obs(env, seed: int) -> np.ndarray:
    out = env.reset(seed=int(seed))
    obs = out[0] if isinstance(out, tuple) else out
    return np.asarray(obs, dtype=np.float32)


def sample_actions(rng: np.random.Generator, n: int, k: int, action_dim: int) -> np.ndarray:
    """Mixture action bank with aggressive and conservative candidates."""

    modes = rng.choice(3, size=(n, k), p=[0.45, 0.35, 0.20])
    actions = np.empty((n, k, action_dim), dtype=np.float32)
    low = rng.normal(0.0, 0.22, size=(n, k, action_dim))
    high = rng.uniform(-1.0, 1.0, size=(n, k, action_dim))
    axis = rng.normal(0.0, 0.08, size=(n, k, action_dim))
    axis[..., 0] += rng.choice([-0.85, 0.85], size=(n, k))
    actions[modes == 0] = low[modes == 0]
    actions[modes == 1] = high[modes == 1]
    actions[modes == 2] = axis[modes == 2]
    return np.clip(actions, -1.0, 1.0).astype(np.float32)


def continuation_action(rng: np.random.Generator, action_dim: int) -> np.ndarray:
    if rng.random() < 0.65:
        action = rng.uniform(-1.0, 1.0, size=action_dim)
    else:
        action = rng.normal(0.0, 0.35, size=action_dim)
    return np.clip(action, -1.0, 1.0).astype(np.float32)


def sample_prefixes(
    rng: np.random.Generator,
    n: int,
    prefix_len: int,
    action_dim: int,
) -> np.ndarray:
    prefixes = np.empty((n, prefix_len, action_dim), dtype=np.float32)
    for i in range(n):
        for t in range(prefix_len):
            prefixes[i, t] = continuation_action(rng, action_dim)
    return prefixes


def replay_prefix_state(env, seed: int, prefix: np.ndarray) -> np.ndarray:
    obs = reset_obs(env, seed)
    for action in prefix:
        obs, _, terminated, truncated, _ = env.step(action)
        obs = np.asarray(obs, dtype=np.float32)
        if terminated or truncated:
            break
    return obs


def rollout_residual_cost(
    env_id: str,
    seeds: np.ndarray,
    prefixes: np.ndarray,
    actions: np.ndarray,
    branches: int,
    horizon: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Reset to each query seed, execute one candidate, then continue."""

    n, k, action_dim = actions.shape
    costs = np.zeros((n, k), dtype=np.float32)
    env = make_env(env_id)
    for i, seed in enumerate(seeds):
        for j in range(k):
            branch_costs = []
            for b in range(branches):
                reset_obs(env, int(seed))
                for prefix_action in prefixes[i]:
                    _, _, terminated, truncated, _ = env.step(prefix_action)
                    if terminated or truncated:
                        break
                _, _, terminated, truncated, info = env.step(actions[i, j])
                total_cost = float(info.get("cost", 0.0))
                if not (terminated or truncated):
                    for _ in range(horizon - 1):
                        cont = continuation_action(rng, action_dim)
                        _, _, terminated, truncated, info = env.step(cont)
                        total_cost += float(info.get("cost", 0.0))
                        if terminated or truncated:
                            break
                branch_costs.append(total_cost)
            costs[i, j] = float(np.mean(branch_costs))
    env.close()
    return costs


def collect_model_data(
    env_id: str,
    rng: np.random.Generator,
    n_model: int,
    horizon: int,
    prefix_len: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    env = make_env(env_id)
    obs0 = reset_obs(env, 0)
    action_dim = int(env.action_space.shape[0])
    obs_dim = int(obs0.shape[0])
    states = np.empty((n_model, obs_dim), dtype=np.float32)
    actions = np.empty((n_model, action_dim), dtype=np.float32)
    rewards = np.empty(n_model, dtype=np.float32)
    residual_costs = np.empty(n_model, dtype=np.float32)
    for idx in range(n_model):
        seed = 10_000_000 + idx
        prefix = sample_prefixes(rng, 1, prefix_len, action_dim)[0]
        obs = replay_prefix_state(env, seed, prefix)
        act = sample_actions(rng, 1, 1, action_dim)[0, 0]
        _, reward, terminated, truncated, info = env.step(act)
        total_cost = float(info.get("cost", 0.0))
        if not (terminated or truncated):
            for _ in range(horizon - 1):
                cont = continuation_action(rng, action_dim)
                _, _, terminated, truncated, info = env.step(cont)
                total_cost += float(info.get("cost", 0.0))
                if terminated or truncated:
                    break
        states[idx] = obs
        actions[idx] = act
        rewards[idx] = float(reward)
        residual_costs[idx] = total_cost
    env.close()
    return states, actions, rewards, residual_costs


def fit_score_models(
    states: np.ndarray,
    actions: np.ndarray,
    rewards: np.ndarray,
    residual_costs: np.ndarray,
    seed: int,
):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler

    x = np.concatenate([states, actions], axis=1)
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)
    reward_model = HistGradientBoostingRegressor(
        max_iter=120,
        learning_rate=0.06,
        max_leaf_nodes=31,
        random_state=seed,
    )
    cost_model = HistGradientBoostingRegressor(
        max_iter=120,
        learning_rate=0.06,
        max_leaf_nodes=31,
        random_state=seed + 1,
    )
    reward_model.fit(x_scaled, rewards)
    cost_model.fit(x_scaled, residual_costs)
    return scaler, reward_model, cost_model


def score_bank(
    scaler,
    reward_model,
    cost_model,
    states: np.ndarray,
    actions: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    n, k, action_dim = actions.shape
    x_state = np.repeat(states[:, None, :], k, axis=1).reshape(n * k, -1)
    x_action = actions.reshape(n * k, action_dim)
    x = scaler.transform(np.concatenate([x_state, x_action], axis=1))
    reward = reward_model.predict(x).reshape(n, k)
    cost_pred = cost_model.predict(x).reshape(n, k)
    action_norm = np.linalg.norm(x_action, axis=1).reshape(n, k)
    support = np.exp(-0.5 * (action_norm / 0.45) ** 2)

    reward_q = np.quantile(reward, [0.02, 0.98])
    cost_q = np.quantile(cost_pred, [0.02, 0.98])
    reward_norm = (reward - reward_q[0]) / max(reward_q[1] - reward_q[0], 1e-6)
    reward_norm = np.clip(reward_norm, 0.0, 1.0)
    aggressive_bonus = 1.0 - support
    proposer_score = 0.62 * reward_norm + 0.38 * aggressive_bonus
    safety = (cost_pred - cost_q[0]) / max(cost_q[1] - cost_q[0], 1e-6)
    return (
        np.clip(proposer_score, 0.0, 1.0).astype(np.float32),
        np.clip(safety, 0.0, 1.0).astype(np.float32),
        np.clip(support, 0.0, 1.0).astype(np.float32),
    )


def choose_fallback_index(reward: np.ndarray, safety: np.ndarray, support: np.ndarray) -> np.ndarray:
    eligible = (support >= 0.45) & (safety <= 0.45)
    score = np.where(eligible, reward + 0.15 * support - 0.20 * safety, -np.inf)
    missing = ~np.isfinite(score).any(axis=1)
    if missing.any():
        score[missing] = support[missing] - 0.30 * safety[missing]
    return np.argmax(score, axis=1)


def build_bank(
    env_id: str,
    rng: np.random.Generator,
    seeds: np.ndarray,
    prefixes: np.ndarray,
    k: int,
    branches: int,
    horizon: int,
    residual_budget: float,
    scaler,
    reward_model,
    cost_model,
) -> EnvBank:
    env = make_env(env_id)
    states = np.stack(
        [replay_prefix_state(env, int(seed), prefixes[idx]) for idx, seed in enumerate(seeds)]
    ).astype(np.float32)
    action_dim = int(env.action_space.shape[0])
    env.close()

    actions = sample_actions(rng, len(seeds), k, action_dim)
    reward, safety, support = score_bank(scaler, reward_model, cost_model, states, actions)
    residual_cost = rollout_residual_cost(env_id, seeds, prefixes, actions, branches, horizon, rng)
    failure = residual_cost > residual_budget
    fallback = choose_fallback_index(reward, safety, support)
    return EnvBank(
        seeds=seeds.astype(np.int64),
        prefixes=prefixes.astype(np.float32),
        state=states,
        candidate_actions=actions,
        reward_scores=reward,
        safety_scores=safety,
        support_scores=support,
        residual_cost=residual_cost,
        residual_failure=failure,
        fallback_index=fallback,
    )


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
    bank: EnvBank,
    eligible: np.ndarray,
    name: str,
    selected_rule: Optional[Dict[str, float]] = None,
) -> AuditorResult:
    reward = bank.reward_scores
    failure = bank.residual_failure
    issued, selected = select_best_by_reward(reward, eligible)
    rows = np.arange(reward.shape[0])
    original = reward.argmax(axis=1)
    chosen = np.where(issued, selected, bank.fallback_index)
    realized_reward = reward[rows, chosen]
    realized_failure = failure[rows, chosen]
    false_when_issued = np.zeros_like(issued, dtype=bool)
    false_when_issued[issued] = failure[rows[issued], selected[issued]]
    issued_count = int(issued.sum())
    failures = int(false_when_issued.sum())
    risk = failures / issued_count if issued_count else 0.0
    return AuditorResult(
        name=name,
        selected_false_certification=float(risk),
        claim_yield=float(issued.mean()),
        normalized_reward=float(realized_reward.mean()),
        fallback_rate=float((~issued).mean()),
        support_rejection_rate=float((chosen != original).mean()),
        episode_violation_rate=float(realized_failure.mean()),
        issued=issued_count,
        failures=failures,
        selected_rule=selected_rule,
    )


def threshold_grid(x: np.ndarray, n_grid: int, low: float = 0.02, high: float = 0.98) -> np.ndarray:
    return np.unique(np.quantile(x.reshape(-1), np.linspace(low, high, n_grid)))


def fit_candidate_threshold(
    audit: EnvBank,
    alpha: float,
    delta: float,
    thresholds: np.ndarray,
) -> Optional[float]:
    candidates = []
    for tau in thresholds:
        mask = audit.safety_scores <= tau
        n = int(mask.sum())
        f = int((audit.residual_failure & mask).sum())
        risk_ucb = one_sided_ucb(f, n, len(thresholds), delta)
        if risk_ucb <= alpha:
            reward = float(audit.reward_scores[mask].mean()) if n else -np.inf
            candidates.append((reward, float(tau)))
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1]))[1]


def fit_reward_bin(audit: EnvBank, n_bins: int, alpha: float, delta: float) -> Dict[str, np.ndarray]:
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


def eval_reward_bin(bank: EnvBank, certifier: Dict[str, np.ndarray]) -> np.ndarray:
    edges = certifier["edges"]
    certified = certifier["certified"]
    bin_id = np.clip(np.searchsorted(edges, bank.reward_scores, side="right") - 1, 0, len(certified) - 1)
    return certified[bin_id]


def fit_rank(audit: EnvBank, alpha: float, delta: float) -> np.ndarray:
    order = np.argsort(-audit.reward_scores, axis=1)
    ranked_failure = np.take_along_axis(audit.residual_failure, order, axis=1)
    k = ranked_failure.shape[1]
    certified = np.zeros(k, dtype=bool)
    for rank in range(k):
        certified[rank] = one_sided_ucb(int(ranked_failure[:, rank].sum()), ranked_failure.shape[0], k, delta) <= alpha
    return certified


def eval_rank(bank: EnvBank, certified_rank: np.ndarray) -> np.ndarray:
    order = np.argsort(-bank.reward_scores, axis=1)
    eligible_ranked = np.repeat(certified_rank[None, :], bank.reward_scores.shape[0], axis=0)
    eligible = np.zeros_like(eligible_ranked, dtype=bool)
    np.put_along_axis(eligible, order, eligible_ranked, axis=1)
    return eligible


def fit_selected_rule_family(
    audit: EnvBank,
    rules: Iterable[Tuple[float, float]],
    alpha: float,
    gamma: float,
    delta: float,
    use_support: bool,
) -> Optional[Dict[str, float]]:
    rules = list(rules)
    candidates: List[Dict[str, float]] = []
    for safety_tau, support_tau in rules:
        eligible = audit.safety_scores <= safety_tau
        if use_support:
            eligible &= audit.support_scores >= support_tau
        evaluated = evaluate_eligible(audit, eligible, "audit")
        risk_ucb = one_sided_ucb(evaluated.failures, evaluated.issued, len(rules), delta)
        ylcb = yield_lcb(evaluated.issued, audit.reward_scores.shape[0], len(rules), delta)
        if risk_ucb <= alpha and ylcb >= gamma:
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


def build_auditors(audit: EnvBank, test: EnvBank, cfg: DSRLPilotConfig) -> List[AuditorResult]:
    n, k = test.reward_scores.shape
    results: List[AuditorResult] = [
        evaluate_eligible(test, np.ones((n, k), dtype=bool), "none_original_proposer")
    ]

    safety_thresholds = threshold_grid(audit.safety_scores, 80)
    tau = fit_candidate_threshold(audit, cfg.alpha, cfg.delta, safety_thresholds)
    eligible = np.zeros((n, k), dtype=bool) if tau is None else (test.safety_scores <= tau)
    results.append(
        evaluate_eligible(test, eligible, "global_candidate_cp", None if tau is None else {"safety_tau": float(tau)})
    )

    reward_cert = fit_reward_bin(audit, 20, cfg.alpha, cfg.delta)
    results.append(
        evaluate_eligible(
            test,
            eval_reward_bin(test, reward_cert),
            "reward_bin_ucb_20",
            {"certified_bins": int(reward_cert["certified"].sum())},
        )
    )

    rank_cert = fit_rank(audit, cfg.alpha, cfg.delta)
    results.append(
        evaluate_eligible(
            test,
            eval_rank(test, rank_cert),
            "rank_bin_ucb",
            {
                "certified_ranks": int(rank_cert.sum()),
                "first_certified_rank": int(np.flatnonzero(rank_cert)[0] + 1) if rank_cert.any() else -1,
            },
        )
    )

    crc_rules = [(float(x), 0.0) for x in safety_thresholds]
    crc_rule = fit_selected_rule_family(audit, crc_rules, cfg.alpha, cfg.gamma, cfg.delta, use_support=False)
    eligible = np.zeros((n, k), dtype=bool) if crc_rule is None else (test.safety_scores <= crc_rule["safety_tau"])
    results.append(evaluate_eligible(test, eligible, "crc_style_safety_threshold", crc_rule))

    support_thresholds = np.unique(
        np.concatenate([[0.0], np.quantile(audit.support_scores.reshape(-1), np.linspace(0.10, 0.90, 17))])
    )
    accs_rules = [(float(st), float(su)) for st in safety_thresholds[::2] for su in support_thresholds]
    accs_rule = fit_selected_rule_family(audit, accs_rules, cfg.alpha, cfg.gamma, cfg.delta, use_support=True)
    eligible = (
        np.zeros((n, k), dtype=bool)
        if accs_rule is None
        else (test.safety_scores <= accs_rule["safety_tau"]) & (test.support_scores >= accs_rule["support_tau"])
    )
    results.append(evaluate_eligible(test, eligible, "accs_v0_support_safety", accs_rule))

    oracle = test.residual_failure == 0
    results.append(evaluate_eligible(test, oracle, "oracle_residual_label"))
    return results


def save_query_bank(path: Path, audit: EnvBank, test: EnvBank, residual_budget: float) -> None:
    np.savez_compressed(
        path,
        residual_budget=np.array([residual_budget], dtype=np.float32),
        audit_seeds=audit.seeds,
        audit_prefixes=audit.prefixes,
        audit_state=audit.state,
        audit_candidate_actions=audit.candidate_actions,
        audit_reward_scores=audit.reward_scores,
        audit_safety_scores=audit.safety_scores,
        audit_support_scores=audit.support_scores,
        audit_residual_cost=audit.residual_cost,
        audit_residual_failure=audit.residual_failure,
        test_seeds=test.seeds,
        test_prefixes=test.prefixes,
        test_state=test.state,
        test_candidate_actions=test.candidate_actions,
        test_reward_scores=test.reward_scores,
        test_safety_scores=test.safety_scores,
        test_support_scores=test.support_scores,
        test_residual_cost=test.residual_cost,
        test_residual_failure=test.residual_failure,
    )


def make_report(payload: Dict[str, object], out_md: Path) -> None:
    cols = [
        "name",
        "selected_false_certification",
        "claim_yield",
        "normalized_reward",
        "fallback_rate",
        "support_rejection_rate",
        "episode_violation_rate",
    ]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in payload["auditors"]:
        values = []
        for col in cols:
            value = row[col]
            values.append(f"{value:.4f}" if isinstance(value, float) else str(value))
        lines.append("| " + " | ".join(values) + " |")
    text = f"""# DSRL Environment Pilot Server Report

Protocol version: `{payload["protocol_version"]}`

Environment: `{payload["env"]}`

Proposer: `{payload["proposer"]}`

Residual label protocol: `{payload["residual_label_protocol"]}`

Residual budget: `{payload["residual_budget"]:.6f}`

## Main Metrics

{chr(10).join(lines)}

## Interpretation

This is the first real-environment bridge. It uses the DSRL simulator and
project-generated query banks because the public DSRL HDF5 endpoint is not
reachable from the server. Treat it as a systems/protocol pilot before CAPS or
official-dataset experiments.
"""
    out_md.write_text(text, encoding="utf-8")


def run_pilot(cfg: DSRLPilotConfig, out_json: Path, out_md: Path) -> Dict[str, object]:
    rng = np.random.default_rng(cfg.seed)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    states, actions, rewards, model_residual_costs = collect_model_data(
        cfg.env_id, rng, cfg.n_model, cfg.horizon, cfg.prefix_len
    )
    scaler, reward_model, cost_model = fit_score_models(states, actions, rewards, model_residual_costs, cfg.seed)

    tune_seeds = np.arange(1_000_000, 1_000_000 + cfg.n_tune, dtype=np.int64)
    tune_prefixes = sample_prefixes(rng, len(tune_seeds), cfg.prefix_len, actions.shape[1])
    tune_actions = sample_actions(rng, len(tune_seeds), cfg.k, actions.shape[1])
    tune_cost = rollout_residual_cost(
        cfg.env_id, tune_seeds, tune_prefixes, tune_actions, cfg.branches, cfg.horizon, rng
    )
    residual_budget = float(np.quantile(tune_cost.reshape(-1), cfg.risk_quantile))

    audit_seeds = np.arange(2_000_000, 2_000_000 + cfg.n_audit, dtype=np.int64)
    test_seeds = np.arange(3_000_000, 3_000_000 + cfg.n_test, dtype=np.int64)
    audit_prefixes = sample_prefixes(rng, cfg.n_audit, cfg.prefix_len, actions.shape[1])
    test_prefixes = sample_prefixes(rng, cfg.n_test, cfg.prefix_len, actions.shape[1])
    audit = build_bank(
        cfg.env_id,
        rng,
        audit_seeds,
        audit_prefixes,
        cfg.k,
        cfg.branches,
        cfg.horizon,
        residual_budget,
        scaler,
        reward_model,
        cost_model,
    )
    test = build_bank(
        cfg.env_id,
        rng,
        test_seeds,
        test_prefixes,
        cfg.k,
        cfg.branches,
        cfg.horizon,
        residual_budget,
        scaler,
        reward_model,
        cost_model,
    )
    auditors = build_auditors(audit, test, cfg)

    query_bank_file = OUTPUT_DIR / "phase_dsrl_env_query_bank_server.npz"
    if cfg.save_query_bank:
        save_query_bank(query_bank_file, audit, test, residual_budget)

    payload: Dict[str, object] = {
        "protocol_version": PROTOCOL_VERSION,
        "proposer": PROPOSER_NAME,
        "env": cfg.env_id,
        "splits": {"model": cfg.n_model, "tune": cfg.n_tune, "audit": cfg.n_audit, "test": cfg.n_test},
        "query_bank": {
            "file": str(query_bank_file.relative_to(ROOT)) if cfg.save_query_bank else None,
            "n_audit_blocks": cfg.n_audit,
            "n_test_blocks": cfg.n_test,
            "k": cfg.k,
            "state_dim": int(audit.state.shape[1]),
            "action_dim": int(audit.candidate_actions.shape[2]),
            "prefix_len": cfg.prefix_len,
            "seed": cfg.seed,
        },
        "residual_label_protocol": (
            f"DSRL simulator branching: reset {cfg.env_id} by seed, replay prefix_len={cfg.prefix_len}, "
            f"execute candidate action, continue for H={cfg.horizon}, M={cfg.branches} branches; "
            "false if mean residual cost exceeds budget"
        ),
        "residual_budget": residual_budget,
        "diagnostics": {
            "audit_candidate_false_rate": float(audit.residual_failure.mean()),
            "audit_top_reward_false_rate": float(
                audit.residual_failure[np.arange(cfg.n_audit), audit.reward_scores.argmax(axis=1)].mean()
            ),
            "test_candidate_false_rate": float(test.residual_failure.mean()),
            "test_top_reward_false_rate": float(
                test.residual_failure[np.arange(cfg.n_test), test.reward_scores.argmax(axis=1)].mean()
            ),
            "model_residual_cost_mean": float(model_residual_costs.mean()),
            "model_residual_cost_q95": float(np.quantile(model_residual_costs, 0.95)),
        },
        "config": asdict(cfg),
        "auditors": [asdict(result) for result in auditors],
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    make_report(payload, out_md)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DSRLPilotConfig.seed)
    parser.add_argument("--env-id", default=DSRLPilotConfig.env_id)
    parser.add_argument("--k", type=int, default=DSRLPilotConfig.k)
    parser.add_argument("--n-model", type=int, default=DSRLPilotConfig.n_model)
    parser.add_argument("--n-tune", type=int, default=DSRLPilotConfig.n_tune)
    parser.add_argument("--n-audit", type=int, default=DSRLPilotConfig.n_audit)
    parser.add_argument("--n-test", type=int, default=DSRLPilotConfig.n_test)
    parser.add_argument("--branches", type=int, default=DSRLPilotConfig.branches)
    parser.add_argument("--horizon", type=int, default=DSRLPilotConfig.horizon)
    parser.add_argument("--prefix-len", type=int, default=DSRLPilotConfig.prefix_len)
    parser.add_argument("--alpha", type=float, default=DSRLPilotConfig.alpha)
    parser.add_argument("--gamma", type=float, default=DSRLPilotConfig.gamma)
    parser.add_argument("--delta", type=float, default=DSRLPilotConfig.delta)
    parser.add_argument("--risk-quantile", type=float, default=DSRLPilotConfig.risk_quantile)
    parser.add_argument("--no-query-bank", action="store_true")
    parser.add_argument(
        "--out-json",
        type=Path,
        default=OUTPUT_DIR / "phase_dsrl_env_pilot_server.json",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=OUTPUT_DIR / "phase_dsrl_env_pilot_server.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = DSRLPilotConfig(
        seed=args.seed,
        env_id=args.env_id,
        k=args.k,
        n_model=args.n_model,
        n_tune=args.n_tune,
        n_audit=args.n_audit,
        n_test=args.n_test,
        branches=args.branches,
        horizon=args.horizon,
        prefix_len=args.prefix_len,
        alpha=args.alpha,
        gamma=args.gamma,
        delta=args.delta,
        risk_quantile=args.risk_quantile,
        save_query_bank=not args.no_query_bank,
    )
    payload = run_pilot(cfg, args.out_json, args.out_md)
    cols = [
        "name",
        "selected_false_certification",
        "claim_yield",
        "normalized_reward",
        "fallback_rate",
        "support_rejection_rate",
        "episode_violation_rate",
    ]
    for row in payload["auditors"]:
        print(" ".join([str(row["name"])] + [f"{row[c]:.6f}" for c in cols[1:]]))
    print(json.dumps(payload["diagnostics"], indent=2))
    print(f"Wrote {args.out_json}")
    print(f"Wrote {args.out_md}")


if __name__ == "__main__":
    main()
