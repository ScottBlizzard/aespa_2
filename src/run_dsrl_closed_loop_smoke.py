"""Closed-loop DSRL rollout smoke for trained OSRL checkpoints.

This script is the first step toward a true episode-level audit. It verifies
that a trained CPQ or COptiDICE checkpoint can be rolled out online in the DSRL
simulator and that reward/cost accounting works. It does not issue ACCS
certificates yet and should not be reported as an episode-level guarantee.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
PROTOCOL_VERSION = "2026-06-24-closed-loop-smoke"


@dataclass(frozen=True)
class ClosedLoopSmokeConfig:
    algo: str
    checkpoint: Path
    env_id: str = "OfflineCarCircle-v0"
    osrl_root: Path = ROOT / "external" / "OSRL"
    seed: int = 20260624
    episodes: int = 10
    max_steps: int = 300
    cost_limit: float = 20.0
    device: str = "cuda:0"
    deterministic: bool = True
    output: Path = OUTPUT_DIR / "phase_dsrl_closed_loop_smoke.json"


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def make_env(env_id: str, cost_limit: float):
    warnings.filterwarnings("ignore", category=UserWarning)
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import gymnasium as gym  # type: ignore
    import dsrl  # noqa: F401  # type: ignore

    env = gym.make(env_id)
    if hasattr(env, "set_target_cost"):
        env.set_target_cost(cost_limit)
    return env


def seed_action_space(env, seed: int) -> None:
    if hasattr(env.action_space, "seed"):
        env.action_space.seed(int(seed))


def load_model(cfg: ClosedLoopSmokeConfig, obs_dim: int, action_dim: int):
    data_stub = SimpleNamespace(
        observations=np.zeros((1, obs_dim), dtype=np.float32),
        actions=np.zeros((1, action_dim), dtype=np.float32),
    )
    if cfg.algo == "cpq":
        from run_dsrl_cpq_checkpoint_pilot import CPQCheckpointConfig, load_cpq_model

        model_cfg = CPQCheckpointConfig(
            env_id=cfg.env_id,
            checkpoint=resolve_path(cfg.checkpoint),
            osrl_root=resolve_path(cfg.osrl_root),
            cost_limit=int(cfg.cost_limit),
            episode_len=int(cfg.max_steps),
            device=cfg.device,
        )
        model, device, checkpoint = load_cpq_model(data_stub, model_cfg)
    elif cfg.algo == "coptidice":
        from run_dsrl_coptidice_checkpoint_pilot import (
            COptiDICECheckpointConfig,
            load_coptidice_model,
        )

        model_cfg = COptiDICECheckpointConfig(
            env_id=cfg.env_id,
            checkpoint=resolve_path(cfg.checkpoint),
            osrl_root=resolve_path(cfg.osrl_root),
            cost_limit=int(cfg.cost_limit),
            episode_len=int(cfg.max_steps),
            device=cfg.device,
        )
        model, device, checkpoint = load_coptidice_model(data_stub, model_cfg)
    else:
        raise ValueError(f"Unsupported algo: {cfg.algo}")
    return model, device, checkpoint


def reset_env(env, seed: int):
    out = env.reset(seed=int(seed))
    if isinstance(out, tuple):
        return np.asarray(out[0], dtype=np.float32)
    return np.asarray(out, dtype=np.float32)


def rollout_episode(env, model, cfg: ClosedLoopSmokeConfig, episode_idx: int) -> Dict[str, float]:
    obs = reset_env(env, cfg.seed + episode_idx)
    episode_reward = 0.0
    episode_cost = 0.0
    length = 0
    for _ in range(cfg.max_steps):
        action, _ = model.act(obs, deterministic=cfg.deterministic, with_logprob=True)
        action = np.asarray(action, dtype=np.float32)
        action = np.clip(action, env.action_space.low, env.action_space.high)
        obs_next, reward, terminated, truncated, info = env.step(action)
        episode_reward += float(reward)
        episode_cost += float(info.get("cost", 0.0))
        length += 1
        obs = np.asarray(obs_next, dtype=np.float32)
        if bool(terminated) or bool(truncated):
            break
    return {
        "episode": int(episode_idx),
        "reward": float(episode_reward),
        "cost": float(episode_cost),
        "length": int(length),
        "violation": bool(episode_cost > cfg.cost_limit),
    }


def summarize(env, episodes: List[Dict[str, float]], cost_limit: float) -> Dict[str, float]:
    rewards = np.array([x["reward"] for x in episodes], dtype=np.float64)
    costs = np.array([x["cost"] for x in episodes], dtype=np.float64)
    lengths = np.array([x["length"] for x in episodes], dtype=np.float64)
    normalized_reward = None
    normalized_cost = None
    if hasattr(env, "get_normalized_score"):
        try:
            nr, nc = env.get_normalized_score(float(rewards.mean()), float(costs.mean()))
            normalized_reward = float(nr)
            normalized_cost = float(nc)
        except Exception:
            normalized_reward = None
            normalized_cost = None
    return {
        "episodes": int(len(episodes)),
        "reward_mean": float(rewards.mean()),
        "reward_std": float(rewards.std(ddof=1)) if len(rewards) > 1 else 0.0,
        "cost_mean": float(costs.mean()),
        "cost_std": float(costs.std(ddof=1)) if len(costs) > 1 else 0.0,
        "length_mean": float(lengths.mean()),
        "episode_violation_rate": float((costs > cost_limit).mean()),
        "normalized_reward": normalized_reward,
        "normalized_cost": normalized_cost,
    }


def write_outputs(payload: Dict, output: Path) -> None:
    output = resolve_path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    summary = payload["summary"]
    lines = [
        "# Closed-Loop DSRL Rollout Smoke",
        "",
        "This is an online simulator rollout smoke, not an ACCS certificate audit.",
        "",
        f"- algo: {payload['config']['algo']}",
        f"- env: {payload['config']['env_id']}",
        f"- checkpoint: `{payload['checkpoint']}`",
        f"- episodes: {summary['episodes']}",
        f"- reward mean/std: {summary['reward_mean']:.4f} / {summary['reward_std']:.4f}",
        f"- cost mean/std: {summary['cost_mean']:.4f} / {summary['cost_std']:.4f}",
        f"- violation rate: {summary['episode_violation_rate']:.4f}",
        f"- length mean: {summary['length_mean']:.2f}",
    ]
    if summary["normalized_reward"] is not None:
        lines.append(f"- normalized reward/cost: {summary['normalized_reward']:.4f} / {summary['normalized_cost']:.4f}")
    output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def serialize_config(cfg: ClosedLoopSmokeConfig) -> Dict:
    raw = asdict(cfg)
    return {key: str(value) if isinstance(value, Path) else value for key, value in raw.items()}


def run(cfg: ClosedLoopSmokeConfig) -> Dict:
    env = make_env(cfg.env_id, cfg.cost_limit)
    seed_action_space(env, cfg.seed)
    obs0 = reset_env(env, cfg.seed)
    model, device, checkpoint = load_model(
        cfg,
        obs_dim=int(obs0.shape[0]),
        action_dim=int(env.action_space.shape[0]),
    )
    episodes = [rollout_episode(env, model, cfg, idx) for idx in range(cfg.episodes)]
    summary = summarize(env, episodes, cfg.cost_limit)
    env.close()
    payload = {
        "protocol_version": PROTOCOL_VERSION,
        "scope": "closed-loop rollout smoke only; no certificate emission",
        "config": {
            **serialize_config(cfg),
            "checkpoint": str(resolve_path(cfg.checkpoint)),
            "output": str(resolve_path(cfg.output)),
        },
        "checkpoint": str(checkpoint),
        "device": str(device),
        "summary": summary,
        "episodes": episodes,
    }
    write_outputs(payload, cfg.output)
    return payload


def parse_args() -> ClosedLoopSmokeConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--algo", choices=["cpq", "coptidice"], required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--env-id", default=ClosedLoopSmokeConfig.env_id)
    parser.add_argument("--osrl-root", type=Path, default=ClosedLoopSmokeConfig.osrl_root)
    parser.add_argument("--seed", type=int, default=ClosedLoopSmokeConfig.seed)
    parser.add_argument("--episodes", type=int, default=ClosedLoopSmokeConfig.episodes)
    parser.add_argument("--max-steps", type=int, default=ClosedLoopSmokeConfig.max_steps)
    parser.add_argument("--cost-limit", type=float, default=ClosedLoopSmokeConfig.cost_limit)
    parser.add_argument("--device", default=ClosedLoopSmokeConfig.device)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--output", type=Path, default=ClosedLoopSmokeConfig.output)
    args = parser.parse_args()
    return ClosedLoopSmokeConfig(
        algo=args.algo,
        checkpoint=args.checkpoint,
        env_id=args.env_id,
        osrl_root=args.osrl_root,
        seed=args.seed,
        episodes=args.episodes,
        max_steps=args.max_steps,
        cost_limit=args.cost_limit,
        device=args.device,
        deterministic=not args.stochastic,
        output=args.output,
    )


def main() -> None:
    cfg = parse_args()
    payload = run(cfg)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    if str(Path(__file__).resolve().parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
