"""Official DSRL pilot with a trained OSRL CPQ checkpoint proposer.

For each anchor state, the CPQ stochastic actor proposes a pool of actions.
Each proposal is mapped to nearby logged actions from the official DSRL HDF5
dataset so residual-cost labels remain observable. The resulting fixed query
bank is evaluated with the same auditor matrix as the CAPSIQL checkpoint pilot.
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
    / "cpq_smoke_logs"
    / "OfflineCarCircle-v0-cost-20"
    / "cpq_car_smoke_seed20260624_v2"
    / "cpq_car_smoke_seed20260624_v2"
    / "checkpoint"
    / "model.pt"
)


@dataclass(frozen=True)
class CPQCheckpointConfig:
    seed: int = 20260624
    env_id: str = "OfflineCarCircle-v0"
    checkpoint: Path = DEFAULT_CHECKPOINT
    osrl_root: Path = ROOT / "external" / "OSRL"
    k: int = 64
    proposal_samples: int = 64
    n_audit: int = 9000
    n_test: int = 12000
    horizon: int = 40
    neighbor_pool: int = 512
    alpha: float = 0.05
    gamma: float = 0.05
    delta: float = 0.05
    risk_quantile: float = 0.93
    reward_risk_bonus: float = 0.0
    reward_support_bonus: float = 0.10
    model_reward_weight: float = 1.0
    model_cost_weight: float = 0.0
    a_hidden_sizes: str = "256,256"
    c_hidden_sizes: str = "256,256"
    vae_hidden_sizes: int = 400
    sample_action_num: int = 10
    max_action: float = 1.0
    cost_limit: int = 20
    episode_len: int = 300
    gamma_rl: float = 0.99
    tau: float = 0.005
    beta: float = 0.5
    num_q: int = 2
    num_qc: int = 2
    qc_scalar: float = 1.5
    device: str = "cuda:0"
    batch_size_eval: int = 8192
    enable_split_accs: bool = False
    save_query_bank: bool = True


def parse_int_list(text: str) -> List[int]:
    values = [int(float(x)) for x in text.split(",") if x.strip()]
    if not values:
        raise ValueError("Expected at least one hidden size")
    return values


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def load_cpq_model(data, cfg: CPQCheckpointConfig):
    import torch

    osrl_root = resolve_path(cfg.osrl_root)
    if str(osrl_root) not in sys.path:
        sys.path.insert(0, str(osrl_root))
    from osrl.algorithms import CPQ

    checkpoint = resolve_path(cfg.checkpoint)
    if not checkpoint.exists():
        raise FileNotFoundError(f"Missing CPQ checkpoint: {checkpoint}")

    device = torch.device(cfg.device if torch.cuda.is_available() and cfg.device.startswith("cuda") else "cpu")
    model = CPQ(
        state_dim=int(data.observations.shape[1]),
        action_dim=int(data.actions.shape[1]),
        max_action=float(cfg.max_action),
        a_hidden_sizes=parse_int_list(cfg.a_hidden_sizes),
        c_hidden_sizes=parse_int_list(cfg.c_hidden_sizes),
        vae_hidden_sizes=int(cfg.vae_hidden_sizes),
        sample_action_num=int(cfg.sample_action_num),
        gamma=float(cfg.gamma_rl),
        tau=float(cfg.tau),
        beta=float(cfg.beta),
        num_q=int(cfg.num_q),
        num_qc=int(cfg.num_qc),
        qc_scalar=float(cfg.qc_scalar),
        cost_limit=int(cfg.cost_limit),
        episode_len=int(cfg.episode_len),
        device=str(device),
    )
    payload = torch.load(checkpoint, map_location=device)
    state = payload["model_state"] if isinstance(payload, dict) and "model_state" in payload else payload
    model.load_state_dict(state, strict=True)
    return model.eval(), str(device), checkpoint


def propose_actor_actions(
    model,
    states: np.ndarray,
    device: str,
    batch_size: int,
    proposal_samples: int,
    seed: int,
) -> np.ndarray:
    import torch

    torch.manual_seed(seed)
    chunks: List[np.ndarray] = []
    max_action = float(getattr(model, "max_action", 1.0))
    with torch.no_grad():
        for start in range(0, len(states), batch_size):
            obs = torch.as_tensor(states[start : start + batch_size], dtype=torch.float32, device=device)
            repeated = obs[:, None, :].expand(-1, proposal_samples, -1).reshape(-1, obs.shape[1])
            sampled, _ = model._actor_forward(repeated, deterministic=False, with_logprob=False)
            deterministic, _ = model._actor_forward(obs, deterministic=True, with_logprob=False)
            sampled = sampled.reshape(len(obs), proposal_samples, -1)
            sampled[:, 0, :] = deterministic.clamp(-max_action, max_action)
            chunks.append(sampled.detach().cpu().numpy())
    return np.concatenate(chunks, axis=0).astype(np.float32)


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
            reward_q, _ = model.critic.predict(obs_t, act_t)
            cost_q, _ = model.cost_critic.predict(obs_t, act_t)
            reward_chunks.append(reward_q.detach().cpu().numpy())
            cost_chunks.append(cost_q.detach().cpu().numpy())
    reward = np.concatenate(reward_chunks, axis=0).reshape(n, k)
    cost = np.concatenate(cost_chunks, axis=0).reshape(n, k)
    return reward.astype(np.float32), cost.astype(np.float32)


def build_cpq_bank(
    data,
    anchor_idx: np.ndarray,
    source_idx: np.ndarray,
    n_blocks: int,
    residual_budget: float,
    seed: int,
    scaler,
    reward_model,
    cost_model,
    cpq_model,
    device: str,
    cfg: CPQCheckpointConfig,
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
    proposed = propose_actor_actions(
        cpq_model,
        states,
        device,
        cfg.batch_size_eval,
        max(cfg.proposal_samples, cfg.k),
        seed,
    )

    action_dist = np.linalg.norm(neighbor_actions[:, None, :, :] - proposed[:, :, None, :], axis=3)
    action_support_scale = max(float(np.quantile(action_dist, 0.25)), 1e-6)
    action_support = np.exp(-action_dist / action_support_scale)

    reward_raw, safety_raw = score_actions(scaler, reward_model, cost_model, states, neighbor_actions)
    model_reward_raw, model_cost_raw = score_checkpoint_actions(
        cpq_model,
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
    fallback_order = np.argsort(-deployment_score, axis=1)
    for row_idx in range(n_blocks):
        chosen: List[int] = []
        seen = set()
        proposal_order = np.argsort(action_dist[row_idx].min(axis=0))
        for pos in proposal_order:
            item = int(pos)
            if item in seen:
                continue
            seen.add(item)
            chosen.append(item)
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
        "proposal_samples": float(max(cfg.proposal_samples, cfg.k)),
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


def run_pilot(cfg: CPQCheckpointConfig, data_dir: Path, out_json: Path, out_md: Path) -> Dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = dataset_path(cfg.env_id, data_dir)
    data = load_logged_dataset(path, cfg.horizon)
    splits = split_by_episode(data, cfg.seed)
    scaler, reward_model, cost_model = fit_models(data, splits["train"], cfg.seed)
    residual_budget = float(np.quantile(data.residual_cost[splits["tune"]], cfg.risk_quantile))
    cpq_model, device, checkpoint = load_cpq_model(data, cfg)

    audit, audit_diag = build_cpq_bank(
        data,
        splits["audit"],
        splits["audit"],
        cfg.n_audit,
        residual_budget,
        cfg.seed + 10,
        scaler,
        reward_model,
        cost_model,
        cpq_model,
        device,
        cfg,
    )
    test, test_diag = build_cpq_bank(
        data,
        splits["test"],
        splits["test"],
        cfg.n_test,
        residual_budget,
        cfg.seed + 20,
        scaler,
        reward_model,
        cost_model,
        cpq_model,
        device,
        cfg,
    )
    auditors = build_auditors(audit, test, cfg)

    query_bank_file = OUTPUT_DIR / f"phase_dsrl_cpq_checkpoint_query_bank_{cfg.env_id}_server.npz"
    if cfg.save_query_bank:
        save_query_bank(query_bank_file, audit, test, residual_budget)

    payload: Dict[str, object] = {
        "protocol_version": PROTOCOL_VERSION,
        "proposer": "official_dsrl_cpq_checkpoint_proposer_v1",
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
            "steps from the nearest logged action matched to each CPQ actor proposal; "
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
    parser.add_argument("--seed", type=int, default=CPQCheckpointConfig.seed)
    parser.add_argument("--env-id", default=CPQCheckpointConfig.env_id)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--checkpoint", type=Path, default=CPQCheckpointConfig.checkpoint)
    parser.add_argument("--osrl-root", type=Path, default=CPQCheckpointConfig.osrl_root)
    parser.add_argument("--k", type=int, default=CPQCheckpointConfig.k)
    parser.add_argument("--proposal-samples", type=int, default=CPQCheckpointConfig.proposal_samples)
    parser.add_argument("--n-audit", type=int, default=CPQCheckpointConfig.n_audit)
    parser.add_argument("--n-test", type=int, default=CPQCheckpointConfig.n_test)
    parser.add_argument("--horizon", type=int, default=CPQCheckpointConfig.horizon)
    parser.add_argument("--neighbor-pool", type=int, default=CPQCheckpointConfig.neighbor_pool)
    parser.add_argument("--alpha", type=float, default=CPQCheckpointConfig.alpha)
    parser.add_argument("--gamma", type=float, default=CPQCheckpointConfig.gamma)
    parser.add_argument("--delta", type=float, default=CPQCheckpointConfig.delta)
    parser.add_argument("--risk-quantile", type=float, default=CPQCheckpointConfig.risk_quantile)
    parser.add_argument("--reward-risk-bonus", type=float, default=CPQCheckpointConfig.reward_risk_bonus)
    parser.add_argument("--reward-support-bonus", type=float, default=CPQCheckpointConfig.reward_support_bonus)
    parser.add_argument("--model-reward-weight", type=float, default=CPQCheckpointConfig.model_reward_weight)
    parser.add_argument("--model-cost-weight", type=float, default=CPQCheckpointConfig.model_cost_weight)
    parser.add_argument("--a-hidden-sizes", default=CPQCheckpointConfig.a_hidden_sizes)
    parser.add_argument("--c-hidden-sizes", default=CPQCheckpointConfig.c_hidden_sizes)
    parser.add_argument("--vae-hidden-sizes", type=int, default=CPQCheckpointConfig.vae_hidden_sizes)
    parser.add_argument("--sample-action-num", type=int, default=CPQCheckpointConfig.sample_action_num)
    parser.add_argument("--cost-limit", type=int, default=CPQCheckpointConfig.cost_limit)
    parser.add_argument("--device", default=CPQCheckpointConfig.device)
    parser.add_argument("--batch-size-eval", type=int, default=CPQCheckpointConfig.batch_size_eval)
    parser.add_argument("--enable-split-accs", action="store_true")
    parser.add_argument("--no-query-bank", action="store_true")
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = CPQCheckpointConfig(
        seed=args.seed,
        env_id=args.env_id,
        checkpoint=args.checkpoint,
        osrl_root=args.osrl_root,
        k=args.k,
        proposal_samples=args.proposal_samples,
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
        a_hidden_sizes=args.a_hidden_sizes,
        c_hidden_sizes=args.c_hidden_sizes,
        vae_hidden_sizes=args.vae_hidden_sizes,
        sample_action_num=args.sample_action_num,
        cost_limit=args.cost_limit,
        device=args.device,
        batch_size_eval=args.batch_size_eval,
        enable_split_accs=args.enable_split_accs,
        save_query_bank=not args.no_query_bank,
    )
    stem = f"phase_dsrl_cpq_checkpoint_pilot_{cfg.env_id}_server"
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
