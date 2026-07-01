"""Official DSRL pilot with a trained CAPSIQL checkpoint proposer.

The script turns a trained OSRL/CAPS CAPSIQL checkpoint into a fixed query
bank. For each anchor state, CAPSIQL actor heads propose actions; each proposed
action is mapped to nearby logged actions from the official DSRL HDF5 dataset so
that residual-cost labels remain observable. Auditors and output schema match
run_dsrl_dataset_pilot.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from run_dsrl_dataset_pilot import (
    DATA_DIR,
    OUTPUT_DIR,
    PROTOCOL_VERSION,
    ROOT,
    DatasetBank,
    build_auditors,
    dataset_path,
    fit_models,
    load_logged_dataset,
    make_report,
    normalize01,
    save_query_bank,
    score_actions,
    split_by_episode,
)


DEFAULT_CHECKPOINT = (
    ROOT
    / "outputs"
    / "capsiql_car_logs_5"
    / "OfflineCarCircle-v0"
    / "capsiql_car_seed20260624"
    / "capsiql_car_seed20260624"
    / "checkpoint"
    / "model.pt"
)


@dataclass(frozen=True)
class CapsIQLCheckpointConfig:
    seed: int = 20260624
    env_id: str = "OfflineCarCircle-v0"
    checkpoint: Path = DEFAULT_CHECKPOINT
    osrl_root: Path = ROOT / "external" / "OSRL"
    k: int = 64
    n_audit: int = 9000
    n_test: int = 12000
    horizon: int = 40
    neighbor_pool: int = 512
    alpha: float = 0.05
    gamma: float = 0.05
    delta: float = 0.05
    risk_quantile: float = 0.92
    reward_risk_bonus: float = 0.25
    reward_support_bonus: float = 0.10
    model_reward_weight: float = 0.25
    model_cost_weight: float = 0.25
    num_heads: int = 5
    hidden_dim: int = 256
    max_action: float = 1.0
    iql_deterministic: bool = False
    iql_tau: float = 0.7
    iql_tau_cost: float = 0.7
    beta: float = 3.0
    beta_cost: float = 3.0
    tau: float = 0.005
    gamma_iql: float = 0.99
    episode_len: int = 300
    device: str = "cuda:0"
    batch_size_eval: int = 8192
    enable_split_accs: bool = False
    save_query_bank: bool = True


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def load_capsiql_model(data, cfg: CapsIQLCheckpointConfig):
    import torch

    osrl_root = resolve_path(cfg.osrl_root)
    if str(osrl_root) not in sys.path:
        sys.path.insert(0, str(osrl_root))
    from osrl.algorithms import CapsIQL

    checkpoint = resolve_path(cfg.checkpoint)
    if not checkpoint.exists():
        raise FileNotFoundError(f"Missing CAPSIQL checkpoint: {checkpoint}")

    device = torch.device(cfg.device if torch.cuda.is_available() and cfg.device.startswith("cuda") else "cpu")
    model = CapsIQL(
        state_dim=int(data.observations.shape[1]),
        action_dim=int(data.actions.shape[1]),
        max_action=float(cfg.max_action),
        num_heads=int(cfg.num_heads),
        iql_deterministic=bool(cfg.iql_deterministic),
        hidden_dim=int(cfg.hidden_dim),
        iql_tau=float(cfg.iql_tau),
        iql_tau_cost=float(cfg.iql_tau_cost),
        beta=float(cfg.beta),
        beta_cost=float(cfg.beta_cost),
        tau=float(cfg.tau),
        gamma=float(cfg.gamma_iql),
        episode_len=int(cfg.episode_len),
        device=str(device),
    )
    payload = torch.load(checkpoint, map_location=device)
    state = payload["model_state"] if isinstance(payload, dict) and "model_state" in payload else payload
    model.load_state_dict(state, strict=True)
    return model.eval(), str(device), checkpoint


def propose_head_actions(model, states: np.ndarray, device: str, batch_size: int) -> np.ndarray:
    import torch

    actions: List[np.ndarray] = []
    max_action = float(getattr(model, "max_action", 1.0))
    with torch.no_grad():
        for start in range(0, len(states), batch_size):
            obs_t = torch.as_tensor(states[start : start + batch_size], dtype=torch.float32, device=device)
            head_outputs = model.actor(obs_t)
            head_actions = []
            for head_out in head_outputs:
                mean = head_out.mean if hasattr(head_out, "mean") else head_out
                action = torch.clamp(max_action * mean, -max_action, max_action)
                head_actions.append(action)
            actions.append(torch.stack(head_actions, dim=1).detach().cpu().numpy())
    return np.concatenate(actions, axis=0).astype(np.float32)


def score_checkpoint_actions(
    model,
    states: np.ndarray,
    actions: np.ndarray,
    device: str,
    batch_size: int,
) -> Tuple[np.ndarray, np.ndarray]:
    import torch

    n, k, action_dim = actions.shape
    repeated_states = np.repeat(states[:, None, :], k, axis=1).reshape(n * k, -1)
    flat_actions = actions.reshape(n * k, action_dim)
    reward_chunks: List[np.ndarray] = []
    cost_chunks: List[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(flat_actions), batch_size):
            stop = start + batch_size
            obs_t = torch.as_tensor(repeated_states[start:stop], dtype=torch.float32, device=device)
            act_t = torch.as_tensor(flat_actions[start:stop], dtype=torch.float32, device=device)
            reward_q = model.reward_q(obs_t, act_t)
            positive_cost_q = -model.cost_q(obs_t, act_t)
            reward_chunks.append(reward_q.detach().cpu().numpy())
            cost_chunks.append(positive_cost_q.detach().cpu().numpy())
    reward = np.concatenate(reward_chunks, axis=0).reshape(n, k)
    cost = np.concatenate(cost_chunks, axis=0).reshape(n, k)
    return reward.astype(np.float32), cost.astype(np.float32)


def build_capsiql_bank(
    data,
    anchor_idx: np.ndarray,
    source_idx: np.ndarray,
    n_blocks: int,
    residual_budget: float,
    seed: int,
    scaler,
    reward_model,
    cost_model,
    capsiql_model,
    device: str,
    cfg: CapsIQLCheckpointConfig,
) -> Tuple[DatasetBank, Dict[str, float]]:
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import StandardScaler

    rng = np.random.default_rng(seed)
    n_blocks = min(n_blocks, len(anchor_idx))
    anchors = rng.choice(anchor_idx, size=n_blocks, replace=False)

    obs_scaler = StandardScaler()
    source_obs_scaled = obs_scaler.fit_transform(data.observations[source_idx])
    anchor_obs_scaled = obs_scaler.transform(data.observations[anchors])
    pool = min(max(cfg.neighbor_pool, cfg.k), len(source_idx))
    nn = NearestNeighbors(n_neighbors=pool, algorithm="auto")
    nn.fit(source_obs_scaled)
    distances, neighbor_pos = nn.kneighbors(anchor_obs_scaled)
    neighbor_idx = source_idx[neighbor_pos]

    states = data.observations[anchors]
    neighbor_actions = data.actions[neighbor_idx]
    proposed = propose_head_actions(capsiql_model, states, device, cfg.batch_size_eval)
    head_count = proposed.shape[1]

    action_dist = np.linalg.norm(neighbor_actions[:, None, :, :] - proposed[:, :, None, :], axis=3)
    action_support_scale = max(float(np.quantile(action_dist, 0.25)), 1e-6)
    action_support = np.exp(-action_dist / action_support_scale)

    reward_raw, safety_raw = score_actions(scaler, reward_model, cost_model, states, neighbor_actions)
    model_reward_raw, model_cost_raw = score_checkpoint_actions(
        capsiql_model,
        states,
        neighbor_actions,
        device,
        cfg.batch_size_eval,
    )
    support_state = np.exp(-distances / max(float(np.quantile(distances, 0.75)), 1e-6))

    reward_norm = normalize01(reward_raw)
    safety_norm = normalize01(safety_raw)
    model_reward_norm = normalize01(model_reward_raw)
    model_cost_norm = normalize01(model_cost_raw)
    deployment_score = (
        reward_norm
        + cfg.model_reward_weight * model_reward_norm
        - cfg.reward_risk_bonus * safety_norm
        - cfg.model_cost_weight * model_cost_norm
        + cfg.reward_support_bonus * support_state
    )
    auditor_safety = normalize01(safety_raw + cfg.model_cost_weight * model_cost_raw)

    top_pos = np.empty((n_blocks, cfg.k), dtype=np.int64)
    per_head = max(1, int(np.ceil(cfg.k / max(head_count, 1))))
    fallback_order = np.argsort(-deployment_score, axis=1)
    for row_idx in range(n_blocks):
        chosen: List[int] = []
        seen = set()
        for head_idx in range(head_count):
            order = np.lexsort((-deployment_score[row_idx], action_dist[row_idx, head_idx]))
            added = 0
            for pos in order:
                item = int(pos)
                if item in seen:
                    continue
                seen.add(item)
                chosen.append(item)
                added += 1
                if len(chosen) >= cfg.k or added >= per_head:
                    break
            if len(chosen) >= cfg.k:
                break
        if len(chosen) < cfg.k:
            for pos in fallback_order[row_idx]:
                item = int(pos)
                if item in seen:
                    continue
                seen.add(item)
                chosen.append(item)
                if len(chosen) >= cfg.k:
                    break
        top_pos[row_idx] = np.asarray(chosen[: cfg.k], dtype=np.int64)

    rows = np.arange(n_blocks)[:, None]
    selected_sources = neighbor_idx[rows, top_pos]
    selected_action_support = action_support.max(axis=1)[rows, top_pos]
    candidate_actions = data.actions[selected_sources]
    reward_scores = normalize01(deployment_score)[rows, top_pos]
    safety_scores = auditor_safety[rows, top_pos]
    support_scores = (support_state[rows, top_pos] * selected_action_support).astype(np.float32)
    residual_cost = data.residual_cost[selected_sources]
    residual_failure = residual_cost > residual_budget
    fallback_index = np.argmax(support_scores - 0.25 * safety_scores, axis=1)

    diagnostics = {
        "head_count": float(head_count),
        "action_match_distance_mean": float(action_dist.min(axis=2).mean()),
        "action_match_distance_median": float(np.median(action_dist.min(axis=2))),
        "checkpoint_reward_score_mean": float(model_reward_raw.mean()),
        "checkpoint_cost_score_mean": float(model_cost_raw.mean()),
    }
    return (
        DatasetBank(
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
        ),
        diagnostics,
    )


def run_pilot(
    cfg: CapsIQLCheckpointConfig,
    data_dir: Path,
    out_json: Path,
    out_md: Path,
) -> Dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = dataset_path(cfg.env_id, data_dir)
    data = load_logged_dataset(path, cfg.horizon)
    splits = split_by_episode(data, cfg.seed)
    scaler, reward_model, cost_model = fit_models(data, splits["train"], cfg.seed)
    residual_budget = float(np.quantile(data.residual_cost[splits["tune"]], cfg.risk_quantile))
    capsiql_model, device, checkpoint = load_capsiql_model(data, cfg)

    audit, audit_diag = build_capsiql_bank(
        data,
        splits["audit"],
        splits["audit"],
        cfg.n_audit,
        residual_budget,
        cfg.seed + 10,
        scaler,
        reward_model,
        cost_model,
        capsiql_model,
        device,
        cfg,
    )
    test, test_diag = build_capsiql_bank(
        data,
        splits["test"],
        splits["test"],
        cfg.n_test,
        residual_budget,
        cfg.seed + 20,
        scaler,
        reward_model,
        cost_model,
        capsiql_model,
        device,
        cfg,
    )
    auditors = build_auditors(audit, test, cfg)

    query_bank_file = OUTPUT_DIR / f"phase_dsrl_capsiql_checkpoint_query_bank_{cfg.env_id}_server.npz"
    if cfg.save_query_bank:
        save_query_bank(query_bank_file, audit, test, residual_budget)

    payload: Dict[str, object] = {
        "protocol_version": PROTOCOL_VERSION,
        "proposer": "official_dsrl_capsiql_checkpoint_proposer_v1",
        "env": cfg.env_id,
        "dataset_file": str(path.relative_to(ROOT)),
        "checkpoint": str(checkpoint.relative_to(ROOT)) if checkpoint.is_relative_to(ROOT) else str(checkpoint),
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
            "steps from the nearest logged action matched to each CAPSIQL head proposal; "
            "false if suffix cost exceeds tune quantile"
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
            "model_reward_weight": float(cfg.model_reward_weight),
            "model_cost_weight": float(cfg.model_cost_weight),
            "device": device,
            "audit": audit_diag,
            "test": test_diag,
        },
        "config": {key: str(value) if isinstance(value, Path) else value for key, value in asdict(cfg).items()},
        "auditors": [asdict(result) for result in auditors],
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    make_report(payload, out_md)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=CapsIQLCheckpointConfig.seed)
    parser.add_argument("--env-id", default=CapsIQLCheckpointConfig.env_id)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--checkpoint", type=Path, default=CapsIQLCheckpointConfig.checkpoint)
    parser.add_argument("--osrl-root", type=Path, default=CapsIQLCheckpointConfig.osrl_root)
    parser.add_argument("--k", type=int, default=CapsIQLCheckpointConfig.k)
    parser.add_argument("--n-audit", type=int, default=CapsIQLCheckpointConfig.n_audit)
    parser.add_argument("--n-test", type=int, default=CapsIQLCheckpointConfig.n_test)
    parser.add_argument("--horizon", type=int, default=CapsIQLCheckpointConfig.horizon)
    parser.add_argument("--neighbor-pool", type=int, default=CapsIQLCheckpointConfig.neighbor_pool)
    parser.add_argument("--alpha", type=float, default=CapsIQLCheckpointConfig.alpha)
    parser.add_argument("--gamma", type=float, default=CapsIQLCheckpointConfig.gamma)
    parser.add_argument("--delta", type=float, default=CapsIQLCheckpointConfig.delta)
    parser.add_argument("--risk-quantile", type=float, default=CapsIQLCheckpointConfig.risk_quantile)
    parser.add_argument("--reward-risk-bonus", type=float, default=CapsIQLCheckpointConfig.reward_risk_bonus)
    parser.add_argument("--reward-support-bonus", type=float, default=CapsIQLCheckpointConfig.reward_support_bonus)
    parser.add_argument("--model-reward-weight", type=float, default=CapsIQLCheckpointConfig.model_reward_weight)
    parser.add_argument("--model-cost-weight", type=float, default=CapsIQLCheckpointConfig.model_cost_weight)
    parser.add_argument("--num-heads", type=int, default=CapsIQLCheckpointConfig.num_heads)
    parser.add_argument("--hidden-dim", type=int, default=CapsIQLCheckpointConfig.hidden_dim)
    parser.add_argument("--max-action", type=float, default=CapsIQLCheckpointConfig.max_action)
    parser.add_argument("--device", default=CapsIQLCheckpointConfig.device)
    parser.add_argument("--batch-size-eval", type=int, default=CapsIQLCheckpointConfig.batch_size_eval)
    parser.add_argument("--enable-split-accs", action="store_true")
    parser.add_argument("--no-query-bank", action="store_true")
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = CapsIQLCheckpointConfig(
        seed=args.seed,
        env_id=args.env_id,
        checkpoint=args.checkpoint,
        osrl_root=args.osrl_root,
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
        model_reward_weight=args.model_reward_weight,
        model_cost_weight=args.model_cost_weight,
        num_heads=args.num_heads,
        hidden_dim=args.hidden_dim,
        max_action=args.max_action,
        device=args.device,
        batch_size_eval=args.batch_size_eval,
        enable_split_accs=args.enable_split_accs,
        save_query_bank=not args.no_query_bank,
    )
    stem = f"phase_dsrl_capsiql_checkpoint_pilot_{cfg.env_id}_server"
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
