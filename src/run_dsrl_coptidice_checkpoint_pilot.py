"""Official DSRL pilot with a trained OSRL COptiDICE checkpoint proposer.

For each anchor state, the COptiDICE stochastic actor proposes a pool of
actions. Each proposal is mapped to nearby logged actions from the official
DSRL HDF5 dataset so residual-cost labels remain observable. COptiDICE does
not expose action-conditioned reward/cost critics like CPQ, so this evaluator
uses actor log probability as the checkpoint policy score and keeps the same
auditor matrix as the CAPSIQL/CPQ checkpoint pilots.
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
    / "coptidice_smoke_logs"
    / "OfflineCarCircle-v0-cost-20"
    / "coptidice_car_smoke_seed20260624"
    / "coptidice_car_smoke_seed20260624"
    / "checkpoint"
    / "model.pt"
)


@dataclass(frozen=True)
class COptiDICECheckpointConfig:
    seed: int = 20260624
    env_id: str = "OfflineCarCircle-v0"
    checkpoint: Path = DEFAULT_CHECKPOINT
    osrl_root: Path = ROOT / "external" / "OSRL"
    k: int = 64
    proposal_samples: int = 96
    n_audit: int = 9000
    n_test: int = 12000
    horizon: int = 40
    neighbor_pool: int = 512
    alpha: float = 0.05
    gamma: float = 0.05
    delta: float = 0.05
    risk_quantile: float = 0.92
    reward_risk_bonus: float = 0.0
    reward_support_bonus: float = 0.10
    model_reward_weight: float = 1.0
    model_cost_weight: float = 0.0
    a_hidden_sizes: str = "256,256"
    c_hidden_sizes: str = "256,256"
    max_action: float = 1.0
    cost_limit: int = 20
    episode_len: int = 300
    gamma_rl: float = 0.99
    copt_alpha: float = 0.5
    cost_ub_epsilon: float = 0.01
    f_type: str = "softchi"
    num_nu: int = 2
    num_chi: int = 2
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


def load_coptidice_model(data, cfg: COptiDICECheckpointConfig):
    import torch

    osrl_root = resolve_path(cfg.osrl_root)
    if str(osrl_root) not in sys.path:
        sys.path.insert(0, str(osrl_root))
    from osrl.algorithms import COptiDICE

    checkpoint = resolve_path(cfg.checkpoint)
    if not checkpoint.exists():
        raise FileNotFoundError(f"Missing COptiDICE checkpoint: {checkpoint}")

    device = torch.device(cfg.device if torch.cuda.is_available() and cfg.device.startswith("cuda") else "cpu")
    model = COptiDICE(
        state_dim=int(data.observations.shape[1]),
        action_dim=int(data.actions.shape[1]),
        max_action=float(cfg.max_action),
        f_type=str(cfg.f_type),
        init_state_propotion=1.0,
        observations_std=np.array([0.0], dtype=np.float32),
        actions_std=np.array([0.0], dtype=np.float32),
        a_hidden_sizes=parse_int_list(cfg.a_hidden_sizes),
        c_hidden_sizes=parse_int_list(cfg.c_hidden_sizes),
        gamma=float(cfg.gamma_rl),
        alpha=float(cfg.copt_alpha),
        cost_ub_epsilon=float(cfg.cost_ub_epsilon),
        num_nu=int(cfg.num_nu),
        num_chi=int(cfg.num_chi),
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
            sampled, _ = model.actor.forward(repeated, deterministic=False, with_logprob=False)
            deterministic, _ = model.actor.forward(obs, deterministic=True, with_logprob=False)
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
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    import torch
    import torch.nn.functional as F
    from torch.distributions.normal import Normal

    n, k, action_dim = actions.shape
    repeated_states = np.repeat(states[:, None, :], k, axis=1).reshape(n * k, -1)
    flat_actions = actions.reshape(n * k, action_dim)
    logp_chunks: List[np.ndarray] = []
    nu_chunks: List[np.ndarray] = []
    chi_chunks: List[np.ndarray] = []
    eps = 1e-6
    with torch.no_grad():
        for start in range(0, len(flat_actions), batch_size):
            stop = start + batch_size
            obs_t = torch.as_tensor(repeated_states[start:stop], dtype=torch.float32, device=device)
            act_t = torch.as_tensor(flat_actions[start:stop], dtype=torch.float32, device=device)
            clipped = act_t.clamp(-1.0 + eps, 1.0 - eps)
            pretanh = 0.5 * (torch.log1p(clipped) - torch.log1p(-clipped))

            net_out = model.actor.net(obs_t)
            mu = model.actor.mu_layer(net_out)
            log_std = torch.clamp(model.actor.log_std_layer(net_out), -20, 2)
            dist = Normal(mu, torch.exp(log_std))
            logp = dist.log_prob(pretanh).sum(axis=-1)
            logp -= (2 * (np.log(2) - pretanh - F.softplus(-2 * pretanh))).sum(axis=1)

            nu_s, _ = model.nu_network.predict(obs_t, None)
            chi_s, _ = model.chi_network.predict(obs_t, None)
            logp_chunks.append(logp.detach().cpu().numpy())
            nu_chunks.append(nu_s.detach().cpu().numpy())
            chi_chunks.append(chi_s.detach().cpu().numpy())

    policy_logp = np.concatenate(logp_chunks, axis=0).reshape(n, k)
    state_nu = np.concatenate(nu_chunks, axis=0).reshape(n, k)
    state_chi = np.concatenate(chi_chunks, axis=0).reshape(n, k)
    return policy_logp.astype(np.float32), state_nu.astype(np.float32), state_chi.astype(np.float32)


def build_coptidice_bank(
    data,
    anchor_idx: np.ndarray,
    source_idx: np.ndarray,
    n_blocks: int,
    residual_budget: float,
    seed: int,
    scaler,
    reward_model,
    cost_model,
    coptidice_model,
    device: str,
    cfg: COptiDICECheckpointConfig,
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
        coptidice_model,
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
    policy_logp_raw, state_nu_raw, state_chi_raw = score_checkpoint_actions(
        coptidice_model,
        states,
        neighbor_actions,
        device,
        cfg.batch_size_eval,
    )
    support_state = np.exp(-distances / max(float(np.quantile(distances, 0.75)), 1e-6))

    reward_norm = normalize01(reward_raw)
    safety_norm = normalize01(safety_raw)
    policy_logp_norm = normalize01(policy_logp_raw)
    state_chi_norm = normalize01(state_chi_raw)
    deployment_score = (
        reward_norm
        + cfg.model_reward_weight * policy_logp_norm
        - cfg.reward_risk_bonus * safety_norm
        - cfg.model_cost_weight * state_chi_norm
        + cfg.reward_support_bonus * support_state
    )
    auditor_safety = normalize01(safety_raw + cfg.model_cost_weight * state_chi_raw)

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
        "checkpoint_policy_logp_mean": float(policy_logp_raw.mean()),
        "checkpoint_state_nu_mean": float(state_nu_raw.mean()),
        "checkpoint_state_chi_mean": float(state_chi_raw.mean()),
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


def run_pilot(cfg: COptiDICECheckpointConfig, data_dir: Path, out_json: Path, out_md: Path) -> Dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = dataset_path(cfg.env_id, data_dir)
    data = load_logged_dataset(path, cfg.horizon)
    splits = split_by_episode(data, cfg.seed)
    scaler, reward_model, cost_model = fit_models(data, splits["train"], cfg.seed)
    residual_budget = float(np.quantile(data.residual_cost[splits["tune"]], cfg.risk_quantile))
    coptidice_model, device, checkpoint = load_coptidice_model(data, cfg)

    audit, audit_diag = build_coptidice_bank(
        data,
        splits["audit"],
        splits["audit"],
        cfg.n_audit,
        residual_budget,
        cfg.seed + 10,
        scaler,
        reward_model,
        cost_model,
        coptidice_model,
        device,
        cfg,
    )
    test, test_diag = build_coptidice_bank(
        data,
        splits["test"],
        splits["test"],
        cfg.n_test,
        residual_budget,
        cfg.seed + 20,
        scaler,
        reward_model,
        cost_model,
        coptidice_model,
        device,
        cfg,
    )
    auditors = build_auditors(audit, test, cfg)

    query_bank_file = OUTPUT_DIR / f"phase_dsrl_coptidice_checkpoint_query_bank_{cfg.env_id}_server.npz"
    if cfg.save_query_bank:
        save_query_bank(query_bank_file, audit, test, residual_budget)

    payload: Dict[str, object] = {
        "protocol_version": PROTOCOL_VERSION,
        "proposer": "official_dsrl_coptidice_checkpoint_proposer_v1",
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
            "steps from the nearest logged action matched to each COptiDICE actor proposal; "
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
    parser.add_argument("--seed", type=int, default=COptiDICECheckpointConfig.seed)
    parser.add_argument("--env-id", default=COptiDICECheckpointConfig.env_id)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--checkpoint", type=Path, default=COptiDICECheckpointConfig.checkpoint)
    parser.add_argument("--osrl-root", type=Path, default=COptiDICECheckpointConfig.osrl_root)
    parser.add_argument("--k", type=int, default=COptiDICECheckpointConfig.k)
    parser.add_argument("--proposal-samples", type=int, default=COptiDICECheckpointConfig.proposal_samples)
    parser.add_argument("--n-audit", type=int, default=COptiDICECheckpointConfig.n_audit)
    parser.add_argument("--n-test", type=int, default=COptiDICECheckpointConfig.n_test)
    parser.add_argument("--horizon", type=int, default=COptiDICECheckpointConfig.horizon)
    parser.add_argument("--neighbor-pool", type=int, default=COptiDICECheckpointConfig.neighbor_pool)
    parser.add_argument("--alpha", type=float, default=COptiDICECheckpointConfig.alpha)
    parser.add_argument("--gamma", type=float, default=COptiDICECheckpointConfig.gamma)
    parser.add_argument("--delta", type=float, default=COptiDICECheckpointConfig.delta)
    parser.add_argument("--risk-quantile", type=float, default=COptiDICECheckpointConfig.risk_quantile)
    parser.add_argument("--reward-risk-bonus", type=float, default=COptiDICECheckpointConfig.reward_risk_bonus)
    parser.add_argument("--reward-support-bonus", type=float, default=COptiDICECheckpointConfig.reward_support_bonus)
    parser.add_argument("--model-reward-weight", type=float, default=COptiDICECheckpointConfig.model_reward_weight)
    parser.add_argument("--model-cost-weight", type=float, default=COptiDICECheckpointConfig.model_cost_weight)
    parser.add_argument("--a-hidden-sizes", default=COptiDICECheckpointConfig.a_hidden_sizes)
    parser.add_argument("--c-hidden-sizes", default=COptiDICECheckpointConfig.c_hidden_sizes)
    parser.add_argument("--cost-limit", type=int, default=COptiDICECheckpointConfig.cost_limit)
    parser.add_argument("--episode-len", type=int, default=COptiDICECheckpointConfig.episode_len)
    parser.add_argument("--gamma-rl", type=float, default=COptiDICECheckpointConfig.gamma_rl)
    parser.add_argument("--copt-alpha", type=float, default=COptiDICECheckpointConfig.copt_alpha)
    parser.add_argument("--cost-ub-epsilon", type=float, default=COptiDICECheckpointConfig.cost_ub_epsilon)
    parser.add_argument("--f-type", default=COptiDICECheckpointConfig.f_type)
    parser.add_argument("--num-nu", type=int, default=COptiDICECheckpointConfig.num_nu)
    parser.add_argument("--num-chi", type=int, default=COptiDICECheckpointConfig.num_chi)
    parser.add_argument("--device", default=COptiDICECheckpointConfig.device)
    parser.add_argument("--batch-size-eval", type=int, default=COptiDICECheckpointConfig.batch_size_eval)
    parser.add_argument("--enable-split-accs", action="store_true")
    parser.add_argument("--no-query-bank", action="store_true")
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = COptiDICECheckpointConfig(
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
        cost_limit=args.cost_limit,
        episode_len=args.episode_len,
        gamma_rl=args.gamma_rl,
        copt_alpha=args.copt_alpha,
        cost_ub_epsilon=args.cost_ub_epsilon,
        f_type=args.f_type,
        num_nu=args.num_nu,
        num_chi=args.num_chi,
        device=args.device,
        batch_size_eval=args.batch_size_eval,
        enable_split_accs=args.enable_split_accs,
        save_query_bank=not args.no_query_bank,
    )
    stem = f"phase_dsrl_coptidice_checkpoint_pilot_{cfg.env_id}_server"
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
