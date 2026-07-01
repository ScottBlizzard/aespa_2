"""Official DSRL HDF5 dataset pilot with logged residual-cost labels.

This script uses downloaded official DSRL HDF5 files instead of simulator-only
query generation. It builds fixed query banks from nearby logged transitions:
for each anchor state, candidate actions are drawn from nearest logged states,
scored at the anchor state, and labeled by the logged candidate transition's
future cost-to-go.

The goal is a real-data bridge, not a final CAPS result:

    DSRL_DATASET_DIR=/workspace/thymic_project/paper/aaai_2/data/dsrl \
    .venv310/bin/python src/run_dsrl_dataset_pilot.py
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
DATA_DIR = ROOT / "data" / "dsrl"
PROTOCOL_VERSION = "2026-06-23"

DATASETS = {
    "OfflineBallCircle-v0": "SafetyBallCircle-v0-80-886.hdf5",
    "OfflineCarCircle-v0": "SafetyCarCircle-v0-100-1450.hdf5",
    "OfflineDroneCircle-v0": "SafetyDroneCircle-v0-100-1923.hdf5",
}


@dataclass(frozen=True)
class DatasetPilotConfig:
    seed: int = 20260624
    env_id: str = "OfflineBallCircle-v0"
    k: int = 16
    n_audit: int = 5000
    n_test: int = 12000
    horizon: int = 40
    neighbor_pool: int = 96
    alpha: float = 0.05
    gamma: float = 0.35
    delta: float = 0.05
    risk_quantile: float = 0.90
    reward_risk_bonus: float = 0.0
    reward_support_bonus: float = 0.10
    proposer_mode: str = "optimistic"
    budget_lambdas: str = "-0.5,0.0,0.25,0.5,1.0,2.0,4.0,8.0"
    enable_split_accs: bool = False
    save_query_bank: bool = True


@dataclass(frozen=True)
class LoggedDataset:
    observations: np.ndarray
    actions: np.ndarray
    rewards: np.ndarray
    costs: np.ndarray
    terminals: np.ndarray
    timeouts: np.ndarray
    episode_id: np.ndarray
    residual_reward: np.ndarray
    residual_cost: np.ndarray


@dataclass(frozen=True)
class DatasetBank:
    anchor_index: np.ndarray
    source_index: np.ndarray
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


def dataset_path(env_id: str, data_dir: Path) -> Path:
    if env_id not in DATASETS:
        raise ValueError(f"Unknown env_id {env_id}. Known: {sorted(DATASETS)}")
    path = data_dir / DATASETS[env_id]
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Download from "
            f"https://huggingface.co/datasets/YYY-45/DSRL/resolve/main/{DATASETS[env_id]}"
        )
    return path


def load_logged_dataset(path: Path, horizon: int) -> LoggedDataset:
    with h5py.File(path, "r") as h5:
        observations = np.asarray(h5["observations"], dtype=np.float32)
        actions = np.asarray(h5["actions"], dtype=np.float32)
        rewards = np.asarray(h5["rewards"], dtype=np.float32)
        costs = np.asarray(h5["costs"], dtype=np.float32)
        terminals = np.asarray(h5["terminals"], dtype=bool)
        timeouts = np.asarray(h5["timeouts"], dtype=bool)

    ends = terminals | timeouts
    episode_id = np.zeros(len(costs), dtype=np.int64)
    residual_reward = np.zeros(len(costs), dtype=np.float32)
    residual_cost = np.zeros(len(costs), dtype=np.float32)
    start = 0
    eid = 0
    for idx, is_end in enumerate(ends):
        episode_id[idx] = eid
        if is_end or idx == len(costs) - 1:
            stop = idx + 1
            ep_costs = costs[start:stop]
            csum = np.concatenate([[0.0], np.cumsum(ep_costs, dtype=np.float64)])
            rsum = np.concatenate([[0.0], np.cumsum(rewards[start:stop], dtype=np.float64)])
            for local in range(stop - start):
                right = min(stop - start, local + horizon)
                residual_cost[start + local] = float(csum[right] - csum[local])
                residual_reward[start + local] = float(rsum[right] - rsum[local])
            start = stop
            eid += 1

    return LoggedDataset(
        observations=observations,
        actions=actions,
        rewards=rewards,
        costs=costs,
        terminals=terminals,
        timeouts=timeouts,
        episode_id=episode_id,
        residual_reward=residual_reward,
        residual_cost=residual_cost,
    )


def split_by_episode(data: LoggedDataset, seed: int) -> Dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    episodes = np.unique(data.episode_id)
    rng.shuffle(episodes)
    n = len(episodes)
    train_ep = set(episodes[: int(0.45 * n)])
    tune_ep = set(episodes[int(0.45 * n) : int(0.60 * n)])
    audit_ep = set(episodes[int(0.60 * n) : int(0.80 * n)])
    test_ep = set(episodes[int(0.80 * n) :])
    splits = {}
    for name, eps in [
        ("train", train_ep),
        ("tune", tune_ep),
        ("audit", audit_ep),
        ("test", test_ep),
    ]:
        mask = np.fromiter((eid in eps for eid in data.episode_id), dtype=bool, count=len(data.episode_id))
        splits[name] = np.flatnonzero(mask)
    return splits


def fit_models(data: LoggedDataset, train_idx: np.ndarray, seed: int):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler

    x = np.concatenate([data.observations[train_idx], data.actions[train_idx]], axis=1)
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)
    reward_model = HistGradientBoostingRegressor(
        max_iter=160,
        learning_rate=0.05,
        max_leaf_nodes=31,
        random_state=seed,
    )
    cost_model = HistGradientBoostingRegressor(
        max_iter=160,
        learning_rate=0.05,
        max_leaf_nodes=31,
        random_state=seed + 1,
    )
    reward_model.fit(x_scaled, data.residual_reward[train_idx])
    cost_model.fit(x_scaled, data.residual_cost[train_idx])
    return scaler, reward_model, cost_model


def score_actions(
    scaler,
    reward_model,
    cost_model,
    states: np.ndarray,
    actions: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    n, k, action_dim = actions.shape
    repeated_states = np.repeat(states[:, None, :], k, axis=1).reshape(n * k, -1)
    flat_actions = actions.reshape(n * k, action_dim)
    x = scaler.transform(np.concatenate([repeated_states, flat_actions], axis=1))
    reward = reward_model.predict(x).reshape(n, k)
    safety = cost_model.predict(x).reshape(n, k)
    return reward.astype(np.float32), safety.astype(np.float32)


def normalize01(x: np.ndarray, q_low: float = 0.02, q_high: float = 0.98) -> np.ndarray:
    lo, hi = np.quantile(x.reshape(-1), [q_low, q_high])
    return np.clip((x - lo) / max(float(hi - lo), 1e-6), 0.0, 1.0)


def build_bank(
    data: LoggedDataset,
    anchor_idx: np.ndarray,
    source_idx: np.ndarray,
    n_blocks: int,
    k: int,
    neighbor_pool: int,
    residual_budget: float,
    seed: int,
    scaler,
    reward_model,
    cost_model,
    reward_risk_bonus: float,
    reward_support_bonus: float,
    proposer_mode: str,
    budget_lambdas: str,
) -> DatasetBank:
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import StandardScaler

    rng = np.random.default_rng(seed)
    n_blocks = min(n_blocks, len(anchor_idx))
    anchors = rng.choice(anchor_idx, size=n_blocks, replace=False)

    obs_scaler = StandardScaler()
    source_obs_scaled = obs_scaler.fit_transform(data.observations[source_idx])
    anchor_obs_scaled = obs_scaler.transform(data.observations[anchors])
    pool = min(max(neighbor_pool, k), len(source_idx))
    nn = NearestNeighbors(n_neighbors=pool, algorithm="auto")
    nn.fit(source_obs_scaled)
    distances, neighbor_pos = nn.kneighbors(anchor_obs_scaled)
    neighbor_idx = source_idx[neighbor_pos]

    states = data.observations[anchors]
    neighbor_actions = data.actions[neighbor_idx]
    reward_raw, safety_raw = score_actions(scaler, reward_model, cost_model, states, neighbor_actions)
    support_raw = np.exp(-distances / max(float(np.quantile(distances, 0.75)), 1e-6))
    reward_norm = normalize01(reward_raw)
    safety_norm = normalize01(safety_raw)

    deployment_score = np.clip(
        reward_norm + reward_risk_bonus * safety_norm + reward_support_bonus * (1.0 - support_raw),
        0.0,
        None,
    )
    if proposer_mode == "optimistic":
        top_pos = np.argsort(-deployment_score, axis=1)[:, :k]
    elif proposer_mode == "budget_heads":
        lambdas = [float(x) for x in budget_lambdas.split(",") if x.strip()]
        if not lambdas:
            raise ValueError("budget_lambdas must contain at least one float")
        head_scores = [reward_norm - lam * safety_norm + reward_support_bonus * support_raw for lam in lambdas]
        top_pos = np.empty((n_blocks, k), dtype=np.int64)
        fallback_order = np.argsort(-deployment_score, axis=1)
        per_head = max(1, int(np.ceil(k / len(lambdas))))
        for row_idx in range(n_blocks):
            chosen: List[int] = []
            seen = set()
            for score in head_scores:
                order = np.argsort(-score[row_idx])
                added = 0
                for pos in order:
                    item = int(pos)
                    if item in seen:
                        continue
                    seen.add(item)
                    chosen.append(item)
                    added += 1
                    if len(chosen) >= k or added >= per_head:
                        break
                if len(chosen) >= k:
                    break
            if len(chosen) < k:
                for pos in fallback_order[row_idx]:
                    item = int(pos)
                    if item in seen:
                        continue
                    seen.add(item)
                    chosen.append(item)
                    if len(chosen) >= k:
                        break
            top_pos[row_idx] = np.asarray(chosen[:k], dtype=np.int64)
    else:
        raise ValueError(f"Unknown proposer_mode {proposer_mode}")
    rows = np.arange(n_blocks)[:, None]
    selected_sources = neighbor_idx[rows, top_pos]
    candidate_actions = data.actions[selected_sources]
    reward_scores = normalize01(deployment_score)[rows, top_pos]
    safety_scores = safety_norm[rows, top_pos]
    support_scores = support_raw[rows, top_pos]
    residual_cost = data.residual_cost[selected_sources]
    residual_failure = residual_cost > residual_budget
    fallback_index = np.argmax(support_scores - 0.25 * safety_scores, axis=1)

    return DatasetBank(
        anchor_index=anchors.astype(np.int64),
        source_index=selected_sources.astype(np.int64),
        state=states.astype(np.float32),
        candidate_actions=candidate_actions.astype(np.float32),
        reward_scores=reward_scores.astype(np.float32),
        safety_scores=safety_scores.astype(np.float32),
        support_scores=support_scores.astype(np.float32),
        residual_cost=residual_cost.astype(np.float32),
        residual_failure=residual_failure.astype(bool),
        fallback_index=fallback_index.astype(np.int64),
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
    bank: DatasetBank,
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
    audit: DatasetBank,
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


def fit_reward_bin(audit: DatasetBank, n_bins: int, alpha: float, delta: float) -> Dict[str, np.ndarray]:
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


def eval_reward_bin(bank: DatasetBank, certifier: Dict[str, np.ndarray]) -> np.ndarray:
    edges = certifier["edges"]
    certified = certifier["certified"]
    bin_id = np.clip(np.searchsorted(edges, bank.reward_scores, side="right") - 1, 0, len(certified) - 1)
    return certified[bin_id]


def fit_rank(audit: DatasetBank, alpha: float, delta: float) -> np.ndarray:
    order = np.argsort(-audit.reward_scores, axis=1)
    ranked_failure = np.take_along_axis(audit.residual_failure, order, axis=1)
    k = ranked_failure.shape[1]
    certified = np.zeros(k, dtype=bool)
    for rank in range(k):
        certified[rank] = one_sided_ucb(int(ranked_failure[:, rank].sum()), ranked_failure.shape[0], k, delta) <= alpha
    return certified


def eval_rank(bank: DatasetBank, certified_rank: np.ndarray) -> np.ndarray:
    order = np.argsort(-bank.reward_scores, axis=1)
    eligible_ranked = np.repeat(certified_rank[None, :], bank.reward_scores.shape[0], axis=0)
    eligible = np.zeros_like(eligible_ranked, dtype=bool)
    np.put_along_axis(eligible, order, eligible_ranked, axis=1)
    return eligible


def slice_bank(bank: DatasetBank, rows: np.ndarray) -> DatasetBank:
    return DatasetBank(
        anchor_index=bank.anchor_index[rows],
        source_index=bank.source_index[rows],
        state=bank.state[rows],
        candidate_actions=bank.candidate_actions[rows],
        reward_scores=bank.reward_scores[rows],
        safety_scores=bank.safety_scores[rows],
        support_scores=bank.support_scores[rows],
        residual_cost=bank.residual_cost[rows],
        residual_failure=bank.residual_failure[rows],
        fallback_index=bank.fallback_index[rows],
    )


def fit_selected_rule_family(
    audit: DatasetBank,
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


def fit_split_validated_rule_family(
    audit: DatasetBank,
    rules: Iterable[Tuple[float, float]],
    alpha: float,
    gamma: float,
    delta: float,
    use_support: bool,
    seed: int,
) -> Optional[Dict[str, float]]:
    rules = list(rules)
    n_blocks = audit.reward_scores.shape[0]
    if n_blocks < 2:
        return None

    rng = np.random.default_rng(seed)
    perm = rng.permutation(n_blocks)
    split = n_blocks // 2
    select_bank = slice_bank(audit, perm[:split])
    validate_bank = slice_bank(audit, perm[split:])

    selected: List[Dict[str, float]] = []
    for safety_tau, support_tau in rules:
        eligible = select_bank.safety_scores <= safety_tau
        if use_support:
            eligible &= select_bank.support_scores >= support_tau
        evaluated = evaluate_eligible(select_bank, eligible, "select")
        if evaluated.issued <= 0 or evaluated.selected_false_certification > alpha or evaluated.claim_yield < gamma:
            continue
        selected.append(
            {
                "safety_tau": float(safety_tau),
                "support_tau": float(support_tau),
                "select_risk": float(evaluated.selected_false_certification),
                "select_reward": float(evaluated.normalized_reward),
                "select_yield": float(evaluated.claim_yield),
            }
        )
    if not selected:
        return None

    candidate = max(selected, key=lambda item: (item["select_reward"], item["select_yield"]))
    eligible = validate_bank.safety_scores <= candidate["safety_tau"]
    if use_support:
        eligible &= validate_bank.support_scores >= candidate["support_tau"]
    validated = evaluate_eligible(validate_bank, eligible, "validate")
    risk_ucb = one_sided_ucb(validated.failures, validated.issued, 1, delta)
    ylcb = yield_lcb(validated.issued, validate_bank.reward_scores.shape[0], 1, delta)
    if risk_ucb > alpha or ylcb < gamma:
        return None

    return {
        **candidate,
        "validate_risk_ucb": float(risk_ucb),
        "validate_yield_lcb": float(ylcb),
        "validate_reward": float(validated.normalized_reward),
        "validate_yield": float(validated.claim_yield),
    }


def build_auditors(audit: DatasetBank, test: DatasetBank, cfg: DatasetPilotConfig) -> List[AuditorResult]:
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

    if cfg.enable_split_accs:
        accs_split_rule = fit_split_validated_rule_family(
            audit,
            accs_rules,
            cfg.alpha,
            cfg.gamma,
            cfg.delta,
            use_support=True,
            seed=cfg.seed + 1000,
        )
        eligible = (
            np.zeros((n, k), dtype=bool)
            if accs_split_rule is None
            else (test.safety_scores <= accs_split_rule["safety_tau"])
            & (test.support_scores >= accs_split_rule["support_tau"])
        )
        results.append(evaluate_eligible(test, eligible, "accs_v1_split_support_safety", accs_split_rule))

    oracle = test.residual_failure == 0
    results.append(evaluate_eligible(test, oracle, "oracle_residual_label"))
    return results


def save_query_bank(path: Path, audit: DatasetBank, test: DatasetBank, residual_budget: float) -> None:
    np.savez_compressed(
        path,
        residual_budget=np.array([residual_budget], dtype=np.float32),
        audit_anchor_index=audit.anchor_index,
        audit_source_index=audit.source_index,
        audit_state=audit.state,
        audit_candidate_actions=audit.candidate_actions,
        audit_reward_scores=audit.reward_scores,
        audit_safety_scores=audit.safety_scores,
        audit_support_scores=audit.support_scores,
        audit_residual_cost=audit.residual_cost,
        audit_residual_failure=audit.residual_failure,
        test_anchor_index=test.anchor_index,
        test_source_index=test.source_index,
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
    text = f"""# DSRL Official Dataset Pilot Server Report

Protocol version: `{payload["protocol_version"]}`

Environment: `{payload["env"]}`

Dataset file: `{payload["dataset_file"]}`

Residual label protocol: `{payload["residual_label_protocol"]}`

Residual budget: `{payload["residual_budget"]:.6f}`

## Main Metrics

{chr(10).join(lines)}

## Interpretation

This pilot uses official DSRL HDF5 trajectories and logged future cost labels.
It is a real-data bridge for debugging the query-bank/auditor contract before a
full CAPS/OSRL proposer is integrated.
"""
    out_md.write_text(text, encoding="utf-8")


def run_pilot(cfg: DatasetPilotConfig, data_dir: Path, out_json: Path, out_md: Path) -> Dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = dataset_path(cfg.env_id, data_dir)
    data = load_logged_dataset(path, cfg.horizon)
    splits = split_by_episode(data, cfg.seed)
    scaler, reward_model, cost_model = fit_models(data, splits["train"], cfg.seed)
    residual_budget = float(np.quantile(data.residual_cost[splits["tune"]], cfg.risk_quantile))

    audit = build_bank(
        data,
        splits["audit"],
        splits["audit"],
        cfg.n_audit,
        cfg.k,
        cfg.neighbor_pool,
        residual_budget,
        cfg.seed + 10,
        scaler,
        reward_model,
        cost_model,
        cfg.reward_risk_bonus,
        cfg.reward_support_bonus,
        cfg.proposer_mode,
        cfg.budget_lambdas,
    )
    test = build_bank(
        data,
        splits["test"],
        splits["test"],
        cfg.n_test,
        cfg.k,
        cfg.neighbor_pool,
        residual_budget,
        cfg.seed + 20,
        scaler,
        reward_model,
        cost_model,
        cfg.reward_risk_bonus,
        cfg.reward_support_bonus,
        cfg.proposer_mode,
        cfg.budget_lambdas,
    )
    auditors = build_auditors(audit, test, cfg)

    query_bank_file = OUTPUT_DIR / f"phase_dsrl_dataset_query_bank_{cfg.env_id}_server.npz"
    if cfg.save_query_bank:
        save_query_bank(query_bank_file, audit, test, residual_budget)

    payload: Dict[str, object] = {
        "protocol_version": PROTOCOL_VERSION,
        "proposer": "official_dsrl_logged_neighbor_proposer_v1",
        "env": cfg.env_id,
        "dataset_file": str(path.relative_to(ROOT)),
        "splits": {name: int(len(idx)) for name, idx in splits.items()},
        "query_bank": {
            "file": str(query_bank_file.relative_to(ROOT)) if cfg.save_query_bank else None,
            "n_audit_blocks": int(audit.reward_scores.shape[0]),
            "n_test_blocks": int(test.reward_scores.shape[0]),
            "k": cfg.k,
            "neighbor_pool": cfg.neighbor_pool,
            "state_dim": int(data.observations.shape[1]),
            "action_dim": int(data.actions.shape[1]),
            "seed": cfg.seed,
        },
        "residual_label_protocol": (
            f"official DSRL logged trajectory suffix cost: sum cost over H={cfg.horizon} "
            "steps from the candidate transition; false if suffix cost exceeds tune quantile"
        ),
        "residual_budget": residual_budget,
        "diagnostics": {
            "audit_candidate_false_rate": float(audit.residual_failure.mean()),
            "audit_top_reward_false_rate": float(
                audit.residual_failure[np.arange(audit.reward_scores.shape[0]), audit.reward_scores.argmax(axis=1)].mean()
            ),
            "test_candidate_false_rate": float(test.residual_failure.mean()),
            "test_top_reward_false_rate": float(
                test.residual_failure[np.arange(test.reward_scores.shape[0]), test.reward_scores.argmax(axis=1)].mean()
            ),
            "dataset_transition_count": int(len(data.rewards)),
            "dataset_episode_count": int(np.unique(data.episode_id).size),
            "reward_risk_bonus": float(cfg.reward_risk_bonus),
            "reward_support_bonus": float(cfg.reward_support_bonus),
            "proposer_mode": cfg.proposer_mode,
            "budget_lambdas": cfg.budget_lambdas,
        },
        "config": asdict(cfg),
        "auditors": [asdict(result) for result in auditors],
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    make_report(payload, out_md)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DatasetPilotConfig.seed)
    parser.add_argument("--env-id", default=DatasetPilotConfig.env_id, choices=sorted(DATASETS))
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--k", type=int, default=DatasetPilotConfig.k)
    parser.add_argument("--n-audit", type=int, default=DatasetPilotConfig.n_audit)
    parser.add_argument("--n-test", type=int, default=DatasetPilotConfig.n_test)
    parser.add_argument("--horizon", type=int, default=DatasetPilotConfig.horizon)
    parser.add_argument("--neighbor-pool", type=int, default=DatasetPilotConfig.neighbor_pool)
    parser.add_argument("--alpha", type=float, default=DatasetPilotConfig.alpha)
    parser.add_argument("--gamma", type=float, default=DatasetPilotConfig.gamma)
    parser.add_argument("--delta", type=float, default=DatasetPilotConfig.delta)
    parser.add_argument("--risk-quantile", type=float, default=DatasetPilotConfig.risk_quantile)
    parser.add_argument("--reward-risk-bonus", type=float, default=DatasetPilotConfig.reward_risk_bonus)
    parser.add_argument("--reward-support-bonus", type=float, default=DatasetPilotConfig.reward_support_bonus)
    parser.add_argument("--proposer-mode", choices=["optimistic", "budget_heads"], default=DatasetPilotConfig.proposer_mode)
    parser.add_argument("--budget-lambdas", default=DatasetPilotConfig.budget_lambdas)
    parser.add_argument("--enable-split-accs", action="store_true")
    parser.add_argument("--no-query-bank", action="store_true")
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = DatasetPilotConfig(
        seed=args.seed,
        env_id=args.env_id,
        k=args.k,
        n_audit=args.n_audit,
        n_test=args.n_test,
        horizon=args.horizon,
        neighbor_pool=args.neighbor_pool,
        alpha=args.alpha,
        gamma=args.gamma,
        delta=args.delta,
        risk_quantile=args.risk_quantile,
        reward_risk_bonus=args.reward_risk_bonus,
        reward_support_bonus=args.reward_support_bonus,
        proposer_mode=args.proposer_mode,
        budget_lambdas=args.budget_lambdas,
        enable_split_accs=args.enable_split_accs,
        save_query_bank=not args.no_query_bank,
    )
    stem = f"phase_dsrl_dataset_pilot_{cfg.env_id}_server"
    out_json = args.out_json or (OUTPUT_DIR / f"{stem}.json")
    out_md = args.out_md or (OUTPUT_DIR / f"{stem}.md")
    payload = run_pilot(cfg, args.data_dir, out_json, out_md)
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
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
