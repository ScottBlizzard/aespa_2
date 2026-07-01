"""Closed-loop episode-budget diagnostic for trained OSRL checkpoints.

This script upgrades the rollout smoke into an online diagnostic. It fits
certificate-emission rules on audit rollouts and evaluates them on independent
test rollouts from the same simulator. The unit of evaluation is a real online
episode, not a logged episode proxy.

The current rule family is intentionally small: a checkpoint safety score
threshold plus an emission cap per episode. Treat the output as diagnostic
until the protocol is frozen and replicated across seeds.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
PROTOCOL_VERSION = "2026-06-24-closed-loop-episode-budget-v1"


@dataclass(frozen=True)
class ClosedLoopAuditConfig:
    algo: str
    checkpoint: Path
    env_id: str = "OfflineCarCircle-v0"
    osrl_root: Path = ROOT / "external" / "OSRL"
    seed: int = 20260624
    audit_episodes: int = 20
    test_episodes: int = 20
    max_steps: int = 300
    cost_limit: float = 20.0
    caps: str = "1,4,8"
    alpha_ep: float = 0.05
    gamma_ep: float = 0.50
    delta: float = 0.10
    n_thresholds: int = 51
    device: str = "cuda:0"
    deterministic: bool = True
    output: Path = OUTPUT_DIR / "phase_dsrl_closed_loop_audit.json"


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def serialize_config(cfg: ClosedLoopAuditConfig) -> Dict:
    raw = asdict(cfg)
    return {key: str(value) if isinstance(value, Path) else value for key, value in raw.items()}


def parse_caps(text: str) -> List[int]:
    caps = [int(x.strip()) for x in text.split(",") if x.strip()]
    if not caps:
        raise ValueError("At least one cap is required")
    return sorted(set(caps))


def make_env(env_id: str, cost_limit: float):
    warnings.filterwarnings("ignore", category=UserWarning)
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import gymnasium as gym  # type: ignore
    import dsrl  # noqa: F401  # type: ignore

    env = gym.make(env_id)
    if hasattr(env, "set_target_cost"):
        env.set_target_cost(cost_limit)
    if hasattr(env.action_space, "seed"):
        env.action_space.seed(0)
    return env


def reset_env(env, seed: int) -> np.ndarray:
    out = env.reset(seed=int(seed))
    obs = out[0] if isinstance(out, tuple) else out
    return np.asarray(obs, dtype=np.float32)


def load_model(cfg: ClosedLoopAuditConfig, obs_dim: int, action_dim: int):
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


def score_action(algo: str, model, obs: np.ndarray, action: np.ndarray, device: str) -> float:
    import torch

    obs_t = torch.as_tensor(obs[None, :], dtype=torch.float32, device=device)
    act_t = torch.as_tensor(action[None, :], dtype=torch.float32, device=device)
    with torch.no_grad():
        if algo == "cpq":
            cost_q, _ = model.cost_critic.predict(obs_t, act_t)
            return float(cost_q.detach().cpu().numpy().reshape(-1)[0])
        if algo == "coptidice":
            chi_s, _ = model.chi_network.predict(obs_t, None)
            return float(chi_s.detach().cpu().numpy().reshape(-1)[0])
    raise ValueError(f"Unsupported algo: {algo}")


def rollout_episode(env, model, cfg: ClosedLoopAuditConfig, device: str, seed: int) -> Dict:
    obs = reset_env(env, seed)
    rewards: List[float] = []
    costs: List[float] = []
    scores: List[float] = []
    for _ in range(cfg.max_steps):
        action, _ = model.act(obs, deterministic=cfg.deterministic, with_logprob=True)
        action = np.asarray(action, dtype=np.float32)
        action = np.clip(action, env.action_space.low, env.action_space.high)
        scores.append(score_action(cfg.algo, model, obs, action, device))
        obs_next, reward, terminated, truncated, info = env.step(action)
        rewards.append(float(reward))
        costs.append(float(info.get("cost", 0.0)))
        obs = np.asarray(obs_next, dtype=np.float32)
        if bool(terminated) or bool(truncated):
            break
    total_cost = float(np.sum(costs))
    return {
        "seed": int(seed),
        "scores": scores,
        "reward": float(np.sum(rewards)),
        "cost": total_cost,
        "length": int(len(scores)),
        "violation": bool(total_cost > cfg.cost_limit),
    }


def rollout_split(env, model, cfg: ClosedLoopAuditConfig, device: str, start_seed: int, n_episodes: int) -> List[Dict]:
    return [rollout_episode(env, model, cfg, device, start_seed + idx) for idx in range(n_episodes)]


def transformed_scores(episodes: List[Dict], variant: str) -> np.ndarray:
    values = np.concatenate([np.asarray(ep["scores"], dtype=np.float64) for ep in episodes])
    if variant == "score":
        return values
    if variant == "neg_score":
        return -values
    raise ValueError(f"Unsupported score variant: {variant}")


def eligible_mask(scores: Iterable[float], variant: str, tau: float, cap: int) -> np.ndarray:
    values = np.asarray(list(scores), dtype=np.float64)
    if variant == "neg_score":
        values = -values
    eligible = values <= tau
    if cap > 0 and int(eligible.sum()) > cap:
        keep = np.flatnonzero(eligible)[:cap]
        capped = np.zeros_like(eligible, dtype=bool)
        capped[keep] = True
        eligible = capped
    return eligible


def evaluate_rule(episodes: List[Dict], variant: str, tau: float, cap: int) -> Dict[str, float]:
    total_steps = int(sum(ep["length"] for ep in episodes))
    issued_steps = 0
    false_steps = 0
    issued_episodes = 0
    false_episodes = 0
    for ep in episodes:
        issued = eligible_mask(ep["scores"], variant, tau, cap)
        count = int(issued.sum())
        issued_steps += count
        if count:
            issued_episodes += 1
            if bool(ep["violation"]):
                false_episodes += 1
                false_steps += count
    block_risk = false_steps / issued_steps if issued_steps else 0.0
    block_yield = issued_steps / total_steps if total_steps else 0.0
    episode_risk = false_episodes / issued_episodes if issued_episodes else 0.0
    episode_yield = issued_episodes / len(episodes) if episodes else 0.0
    return {
        "block_risk": float(block_risk),
        "block_yield": float(block_yield),
        "episode_false": float(episode_risk),
        "episode_yield": float(episode_yield),
        "issued_steps": int(issued_steps),
        "false_steps": int(false_steps),
        "issued_episodes": int(issued_episodes),
        "false_episodes": int(false_episodes),
        "issued_steps_per_episode": float(issued_steps / max(len(episodes), 1)),
    }


def candidate_thresholds(episodes: List[Dict], variant: str, n_thresholds: int) -> np.ndarray:
    values = transformed_scores(episodes, variant)
    if values.size == 0:
        return np.array([], dtype=np.float64)
    grid = np.linspace(0.02, 0.98, int(n_thresholds))
    return np.unique(np.quantile(values, grid))


def episode_ucb(false_episodes: int, n_episodes: int, n_rules: int, delta: float) -> float:
    eps = math.sqrt(math.log(2.0 * max(n_rules, 1) / delta) / (2.0 * max(n_episodes, 1)))
    return float(min(1.0, false_episodes / max(n_episodes, 1) + eps))


def episode_yield_lcb(issued_episodes: int, n_episodes: int, n_rules: int, delta: float) -> float:
    eps = math.sqrt(math.log(2.0 * max(n_rules, 1) / delta) / (2.0 * max(n_episodes, 1)))
    return float(max(0.0, issued_episodes / max(n_episodes, 1) - eps))


def fit_rules(episodes: List[Dict], cfg: ClosedLoopAuditConfig, caps: List[int]) -> List[Dict]:
    variants = ["score"] if cfg.algo == "cpq" else ["score", "neg_score"]
    thresholds_by_variant = {
        variant: candidate_thresholds(episodes, variant, cfg.n_thresholds) for variant in variants
    }
    n_rules = int(sum(len(thresholds_by_variant[v]) for v in variants) * len(caps))
    selected: List[Dict] = []
    for cap in caps:
        candidates: List[Dict] = []
        for variant in variants:
            for tau in thresholds_by_variant[variant]:
                audit_metrics = evaluate_rule(episodes, variant, float(tau), int(cap))
                risk_ucb = episode_ucb(
                    int(audit_metrics["false_episodes"]),
                    len(episodes),
                    n_rules,
                    cfg.delta,
                )
                yield_lcb = episode_yield_lcb(
                    int(audit_metrics["issued_episodes"]),
                    len(episodes),
                    n_rules,
                    cfg.delta,
                )
                candidates.append(
                    {
                        "variant": variant,
                        "tau": float(tau),
                        "cap": int(cap),
                        "audit": audit_metrics,
                        "episode_risk_ucb": float(risk_ucb),
                        "episode_yield_lcb": float(yield_lcb),
                        "ucb_valid": bool(risk_ucb <= cfg.alpha_ep and yield_lcb >= cfg.gamma_ep),
                    }
                )
        valid = [item for item in candidates if item["ucb_valid"]]
        if valid:
            choice = max(
                valid,
                key=lambda item: (
                    item["audit"]["issued_steps_per_episode"],
                    item["audit"]["block_yield"],
                    -item["audit"]["episode_false"],
                ),
            )
        else:
            empirical = [
                item
                for item in candidates
                if item["audit"]["episode_false"] <= cfg.alpha_ep and item["audit"]["episode_yield"] >= cfg.gamma_ep
            ]
            pool = empirical if empirical else candidates
            choice = max(
                pool,
                key=lambda item: (
                    -item["audit"]["episode_false"],
                    item["audit"]["episode_yield"],
                    item["audit"]["issued_steps_per_episode"],
                ),
            )
            choice = {**choice, "diagnostic_only_reason": "no finite-sample episode-UCB-valid rule on audit split"}
        selected.append(choice)
    return selected


def summarize_rollouts(env, episodes: List[Dict], cost_limit: float) -> Dict[str, float]:
    rewards = np.array([ep["reward"] for ep in episodes], dtype=np.float64)
    costs = np.array([ep["cost"] for ep in episodes], dtype=np.float64)
    lengths = np.array([ep["length"] for ep in episodes], dtype=np.float64)
    normalized_reward = None
    normalized_cost = None
    if hasattr(env, "get_normalized_score"):
        try:
            normalized_reward, normalized_cost = env.get_normalized_score(float(rewards.mean()), float(costs.mean()))
            normalized_reward = float(normalized_reward)
            normalized_cost = float(normalized_cost)
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
    lines = [
        "# Closed-Loop Episode-Budget Diagnostic",
        "",
        "This is an online simulator diagnostic. It is not yet paper evidence unless the rule is UCB-valid and replicated.",
        "",
        f"- algo: {payload['config']['algo']}",
        f"- env: {payload['config']['env_id']}",
        f"- checkpoint: `{payload['checkpoint']}`",
        f"- audit/test episodes: {payload['config']['audit_episodes']} / {payload['config']['test_episodes']}",
        f"- test cost mean: {payload['test_summary']['cost_mean']:.4f}",
        f"- test violation rate: {payload['test_summary']['episode_violation_rate']:.4f}",
        "",
        "| cap | variant | UCB valid | audit ep F/Y | test ep F/Y | test block R/Y | issued steps/ep |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["rules"]:
        audit = row["audit"]
        test = row["test"]
        lines.append(
            f"| {row['cap']} | {row['variant']} | {int(row['ucb_valid'])} | "
            f"{audit['episode_false']:.4f}/{audit['episode_yield']:.4f} | "
            f"{test['episode_false']:.4f}/{test['episode_yield']:.4f} | "
            f"{test['block_risk']:.4f}/{test['block_yield']:.4f} | "
            f"{test['issued_steps_per_episode']:.2f} |"
        )
    output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(cfg: ClosedLoopAuditConfig) -> Dict:
    caps = parse_caps(cfg.caps)
    env = make_env(cfg.env_id, cfg.cost_limit)
    obs0 = reset_env(env, cfg.seed)
    model, device, checkpoint = load_model(
        cfg,
        obs_dim=int(obs0.shape[0]),
        action_dim=int(env.action_space.shape[0]),
    )
    audit = rollout_split(env, model, cfg, device, cfg.seed + 10_000, cfg.audit_episodes)
    test = rollout_split(env, model, cfg, device, cfg.seed + 20_000, cfg.test_episodes)
    selected = fit_rules(audit, cfg, caps)
    rules = []
    for rule in selected:
        test_metrics = evaluate_rule(test, rule["variant"], rule["tau"], rule["cap"])
        rules.append({**rule, "test": test_metrics})
    payload = {
        "protocol_version": PROTOCOL_VERSION,
        "scope": "online closed-loop episode-budget diagnostic",
        "config": {
            **serialize_config(cfg),
            "checkpoint": str(resolve_path(cfg.checkpoint)),
            "output": str(resolve_path(cfg.output)),
        },
        "checkpoint": str(checkpoint),
        "device": str(device),
        "audit_summary": summarize_rollouts(env, audit, cfg.cost_limit),
        "test_summary": summarize_rollouts(env, test, cfg.cost_limit),
        "rules": rules,
    }
    env.close()
    write_outputs(payload, cfg.output)
    return payload


def parse_args() -> ClosedLoopAuditConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--algo", choices=["cpq", "coptidice"], required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--env-id", default=ClosedLoopAuditConfig.env_id)
    parser.add_argument("--osrl-root", type=Path, default=ClosedLoopAuditConfig.osrl_root)
    parser.add_argument("--seed", type=int, default=ClosedLoopAuditConfig.seed)
    parser.add_argument("--audit-episodes", type=int, default=ClosedLoopAuditConfig.audit_episodes)
    parser.add_argument("--test-episodes", type=int, default=ClosedLoopAuditConfig.test_episodes)
    parser.add_argument("--max-steps", type=int, default=ClosedLoopAuditConfig.max_steps)
    parser.add_argument("--cost-limit", type=float, default=ClosedLoopAuditConfig.cost_limit)
    parser.add_argument("--caps", default=ClosedLoopAuditConfig.caps)
    parser.add_argument("--alpha-ep", type=float, default=ClosedLoopAuditConfig.alpha_ep)
    parser.add_argument("--gamma-ep", type=float, default=ClosedLoopAuditConfig.gamma_ep)
    parser.add_argument("--delta", type=float, default=ClosedLoopAuditConfig.delta)
    parser.add_argument("--n-thresholds", type=int, default=ClosedLoopAuditConfig.n_thresholds)
    parser.add_argument("--device", default=ClosedLoopAuditConfig.device)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--output", type=Path, default=ClosedLoopAuditConfig.output)
    args = parser.parse_args()
    return ClosedLoopAuditConfig(
        algo=args.algo,
        checkpoint=args.checkpoint,
        env_id=args.env_id,
        osrl_root=args.osrl_root,
        seed=args.seed,
        audit_episodes=args.audit_episodes,
        test_episodes=args.test_episodes,
        max_steps=args.max_steps,
        cost_limit=args.cost_limit,
        caps=args.caps,
        alpha_ep=args.alpha_ep,
        gamma_ep=args.gamma_ep,
        delta=args.delta,
        n_thresholds=args.n_thresholds,
        device=args.device,
        deterministic=not args.stochastic,
        output=args.output,
    )


def main() -> None:
    payload = run(parse_args())
    print(json.dumps({"test_summary": payload["test_summary"], "rules": payload["rules"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    if str(Path(__file__).resolve().parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
