"""Official DSRL HDF5 pilot with trained multi-head BC proposer.

This is a bridge between the procedural CAPS-style candidate generator and a
full CAPS/OSRL checkpoint. It trains several deterministic policy heads on the
official DSRL HDF5 train split using reward/cost-weighted behavior cloning.
For each audit/test anchor state, each learned head proposes an action; the
script maps those proposed actions to nearby logged actions in a local
state-neighbor pool so residual-cost labels remain observable from the HDF5
trajectories.

The output schema matches run_dsrl_dataset_pilot.py so auditors are comparable.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np

from run_dsrl_dataset_pilot import (
    DATA_DIR,
    OUTPUT_DIR,
    PROTOCOL_VERSION,
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


@dataclass(frozen=True)
class BCHeadsConfig:
    seed: int = 20260624
    env_id: str = "OfflineCarCircle-v0"
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
    head_lambdas: str = "-0.5,0.0,0.25,0.5,1.0,2.0,4.0,8.0"
    train_steps: int = 4000
    batch_size: int = 2048
    hidden_dim: int = 256
    lr: float = 3e-4
    weight_temperature: float = 4.0
    device: str = "cuda:0"
    enable_split_accs: bool = False
    save_query_bank: bool = True


def parse_lambdas(text: str) -> List[float]:
    values = [float(x) for x in text.split(",") if x.strip()]
    if not values:
        raise ValueError("head_lambdas must contain at least one float")
    return values


def normalize_columns(x: np.ndarray) -> np.ndarray:
    lo = x.min()
    hi = x.max()
    return (x - lo) / max(float(hi - lo), 1e-8)


def train_policy_heads(data, train_idx: np.ndarray, cfg: BCHeadsConfig):
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    rng = np.random.default_rng(cfg.seed)
    lambdas = parse_lambdas(cfg.head_lambdas)
    obs = data.observations[train_idx].astype(np.float32)
    act = data.actions[train_idx].astype(np.float32)
    r = normalize_columns(data.residual_reward[train_idx].astype(np.float32))
    c = normalize_columns(data.residual_cost[train_idx].astype(np.float32))

    weights = []
    for lam in lambdas:
        score = r - lam * c
        score = score - np.median(score)
        w = np.exp(np.clip(cfg.weight_temperature * score, -4.0, 4.0))
        weights.append((w / (w.mean() + 1e-8)).astype(np.float32))
    weight_arr = np.stack(weights, axis=1)

    device = torch.device(cfg.device if torch.cuda.is_available() and cfg.device.startswith("cuda") else "cpu")
    obs_t = torch.as_tensor(obs, device=device)
    act_t = torch.as_tensor(act, device=device)
    weight_t = torch.as_tensor(weight_arr, device=device)

    class MultiHeadPolicy(nn.Module):
        def __init__(self, state_dim: int, action_dim: int, hidden_dim: int, n_heads: int):
            super().__init__()
            self.trunk = nn.Sequential(
                nn.Linear(state_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
            )
            self.heads = nn.ModuleList([nn.Linear(hidden_dim, action_dim) for _ in range(n_heads)])

        def forward(self, x):
            z = self.trunk(x)
            return torch.stack([torch.tanh(head(z)) for head in self.heads], dim=1)

    torch.manual_seed(cfg.seed)
    model = MultiHeadPolicy(obs.shape[1], act.shape[1], cfg.hidden_dim, len(lambdas)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=1e-4)

    n = obs.shape[0]
    for step in range(cfg.train_steps):
        batch = rng.integers(0, n, size=cfg.batch_size)
        pred = model(obs_t[batch])
        target = act_t[batch, None, :]
        mse = F.mse_loss(pred, target.expand_as(pred), reduction="none").mean(dim=2)
        loss = (mse * weight_t[batch]).mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if (step + 1) % max(1, cfg.train_steps // 5) == 0:
            print(f"train_step {step + 1}/{cfg.train_steps} loss={float(loss.detach().cpu()):.6f}")

    return model.eval(), str(device), lambdas


def build_bc_head_bank(
    data,
    anchor_idx: np.ndarray,
    source_idx: np.ndarray,
    n_blocks: int,
    residual_budget: float,
    seed: int,
    scaler,
    reward_model,
    cost_model,
    policy,
    device: str,
    cfg: BCHeadsConfig,
) -> DatasetBank:
    import torch
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
    with torch.no_grad():
        proposed = (
            policy(torch.as_tensor(states, dtype=torch.float32, device=device))
            .detach()
            .cpu()
            .numpy()
        )

    neighbor_actions = data.actions[neighbor_idx]
    head_count = proposed.shape[1]
    action_dist = np.linalg.norm(neighbor_actions[:, None, :, :] - proposed[:, :, None, :], axis=3)
    action_support_scale = max(float(np.quantile(action_dist, 0.25)), 1e-6)
    action_support = np.exp(-action_dist / action_support_scale)

    reward_raw, safety_raw = score_actions(scaler, reward_model, cost_model, states, neighbor_actions)
    support_state = np.exp(-distances / max(float(np.quantile(distances, 0.75)), 1e-6))
    reward_norm = normalize01(reward_raw)
    safety_norm = normalize01(safety_raw)
    deployment_score = np.clip(
        reward_norm - cfg.reward_risk_bonus * safety_norm + cfg.reward_support_bonus * support_state,
        0.0,
        None,
    )

    top_pos = np.empty((n_blocks, cfg.k), dtype=np.int64)
    per_head = max(1, int(np.ceil(cfg.k / head_count)))
    fallback_order = np.argsort(-deployment_score, axis=1)
    for row_idx in range(n_blocks):
        chosen: List[int] = []
        seen = set()
        for head_idx in range(head_count):
            # First take actions close to each learned head, with reward score as tie-break.
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
    safety_scores = safety_norm[rows, top_pos]
    support_scores = (support_state[rows, top_pos] * selected_action_support).astype(np.float32)
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


def run_pilot(cfg: BCHeadsConfig, data_dir: Path, out_json: Path, out_md: Path) -> Dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = dataset_path(cfg.env_id, data_dir)
    data = load_logged_dataset(path, cfg.horizon)
    splits = split_by_episode(data, cfg.seed)
    scaler, reward_model, cost_model = fit_models(data, splits["train"], cfg.seed)
    residual_budget = float(np.quantile(data.residual_cost[splits["tune"]], cfg.risk_quantile))
    policy, device, lambdas = train_policy_heads(data, splits["train"], cfg)

    audit = build_bc_head_bank(
        data,
        splits["audit"],
        splits["audit"],
        cfg.n_audit,
        residual_budget,
        cfg.seed + 10,
        scaler,
        reward_model,
        cost_model,
        policy,
        device,
        cfg,
    )
    test = build_bc_head_bank(
        data,
        splits["test"],
        splits["test"],
        cfg.n_test,
        residual_budget,
        cfg.seed + 20,
        scaler,
        reward_model,
        cost_model,
        policy,
        device,
        cfg,
    )
    auditors = build_auditors(audit, test, cfg)

    query_bank_file = OUTPUT_DIR / f"phase_dsrl_bc_heads_query_bank_{cfg.env_id}_server.npz"
    if cfg.save_query_bank:
        save_query_bank(query_bank_file, audit, test, residual_budget)

    payload: Dict[str, object] = {
        "protocol_version": PROTOCOL_VERSION,
        "proposer": "official_dsrl_trained_weighted_bc_heads_v1",
        "env": cfg.env_id,
        "dataset_file": str(path.relative_to(path.parents[2])),
        "splits": {name: int(len(idx)) for name, idx in splits.items()},
        "query_bank": {
            "file": str(query_bank_file) if cfg.save_query_bank else None,
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
            "steps from the nearest logged action matched to each learned-head proposal; "
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
            "head_lambdas": cfg.head_lambdas,
            "train_steps": int(cfg.train_steps),
            "device": device,
        },
        "config": asdict(cfg),
        "auditors": [asdict(result) for result in auditors],
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    make_report(payload, out_md)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=BCHeadsConfig.seed)
    parser.add_argument("--env-id", default=BCHeadsConfig.env_id)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--k", type=int, default=BCHeadsConfig.k)
    parser.add_argument("--n-audit", type=int, default=BCHeadsConfig.n_audit)
    parser.add_argument("--n-test", type=int, default=BCHeadsConfig.n_test)
    parser.add_argument("--horizon", type=int, default=BCHeadsConfig.horizon)
    parser.add_argument("--neighbor-pool", type=int, default=BCHeadsConfig.neighbor_pool)
    parser.add_argument("--alpha", type=float, default=BCHeadsConfig.alpha)
    parser.add_argument("--gamma", type=float, default=BCHeadsConfig.gamma)
    parser.add_argument("--delta", type=float, default=BCHeadsConfig.delta)
    parser.add_argument("--risk-quantile", type=float, default=BCHeadsConfig.risk_quantile)
    parser.add_argument("--reward-risk-bonus", type=float, default=BCHeadsConfig.reward_risk_bonus)
    parser.add_argument("--reward-support-bonus", type=float, default=BCHeadsConfig.reward_support_bonus)
    parser.add_argument("--head-lambdas", default=BCHeadsConfig.head_lambdas)
    parser.add_argument("--train-steps", type=int, default=BCHeadsConfig.train_steps)
    parser.add_argument("--batch-size", type=int, default=BCHeadsConfig.batch_size)
    parser.add_argument("--hidden-dim", type=int, default=BCHeadsConfig.hidden_dim)
    parser.add_argument("--lr", type=float, default=BCHeadsConfig.lr)
    parser.add_argument("--weight-temperature", type=float, default=BCHeadsConfig.weight_temperature)
    parser.add_argument("--device", default=BCHeadsConfig.device)
    parser.add_argument("--no-query-bank", action="store_true")
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = BCHeadsConfig(
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
        head_lambdas=args.head_lambdas,
        train_steps=args.train_steps,
        batch_size=args.batch_size,
        hidden_dim=args.hidden_dim,
        lr=args.lr,
        weight_temperature=args.weight_temperature,
        device=args.device,
        save_query_bank=not args.no_query_bank,
    )
    out_json = args.out_json or OUTPUT_DIR / "phase_dsrl_bc_heads_pilot_server.json"
    out_md = args.out_md or OUTPUT_DIR / "phase_dsrl_bc_heads_pilot_server.md"
    payload = run_pilot(cfg, args.data_dir, out_json, out_md)
    for row in payload["auditors"]:
        print(
            row["name"],
            f"{row['selected_false_certification']:.6f}",
            f"{row['claim_yield']:.6f}",
            f"{row['normalized_reward']:.6f}",
            f"{row['fallback_rate']:.6f}",
            f"{row['support_rejection_rate']:.6f}",
            f"{row['episode_violation_rate']:.6f}",
        )
    print(json.dumps(payload["diagnostics"], indent=2))
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
