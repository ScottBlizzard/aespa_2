"""Pre-registered closed-loop first-cap episode audit.

This is the clean fixed-rule counterpart to ``run_dsrl_closed_loop_audit.py``.
It does not fit a score threshold on audit episodes. For each online episode,
it issues certificates for the first ``cap`` policy steps and audits whether any
issued episode violates the environment cost limit.

The rule is deliberately simple because its finite-sample accounting can use a
plain exact binomial interval over issued episodes without a threshold-family
selection penalty.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np

from run_dsrl_closed_loop_audit import (
    OUTPUT_DIR,
    ROOT,
    load_model,
    make_env,
    parse_caps,
    reset_env,
    resolve_path,
    rollout_split,
    serialize_config,
    summarize_rollouts,
)


PROTOCOL_VERSION = "2026-06-24-closed-loop-fixed-first-cap-v1"


@dataclass(frozen=True)
class FixedCapAuditConfig:
    algo: str
    checkpoint: Path
    env_id: str = "OfflineCarCircle-v0"
    osrl_root: Path = ROOT / "external" / "OSRL"
    seed: int = 20260624
    audit_episodes: int = 100
    test_episodes: int = 100
    max_steps: int = 300
    cost_limit: float = 20.0
    caps: str = "1,4,8"
    device: str = "cuda:0"
    deterministic: bool = True
    output: Path = OUTPUT_DIR / "phase_dsrl_closed_loop_fixed_cap_audit.json"


def evaluate_first_cap(episodes: List[Dict], cap: int) -> Dict[str, float]:
    total_steps = int(sum(ep["length"] for ep in episodes))
    issued_steps = 0
    false_steps = 0
    issued_episodes = 0
    false_episodes = 0
    for ep in episodes:
        count = int(min(max(cap, 0), ep["length"]))
        if count <= 0:
            continue
        issued_episodes += 1
        issued_steps += count
        if bool(ep["violation"]):
            false_episodes += 1
            false_steps += count
    return {
        "block_risk": float(false_steps / issued_steps) if issued_steps else 0.0,
        "block_yield": float(issued_steps / total_steps) if total_steps else 0.0,
        "episode_false": float(false_episodes / issued_episodes) if issued_episodes else 0.0,
        "episode_yield": float(issued_episodes / len(episodes)) if episodes else 0.0,
        "issued_steps": int(issued_steps),
        "false_steps": int(false_steps),
        "issued_episodes": int(issued_episodes),
        "false_episodes": int(false_episodes),
        "issued_steps_per_episode": float(issued_steps / max(len(episodes), 1)),
    }


def write_outputs(payload: Dict, output: Path) -> None:
    output = resolve_path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Closed-Loop Fixed First-Cap Episode Audit",
        "",
        "The rule is pre-registered: issue certificates for the first cap policy steps in every online episode. No score threshold is fit on audit labels.",
        "",
        f"- algo: {payload['config']['algo']}",
        f"- env: {payload['config']['env_id']}",
        f"- checkpoint: `{payload['checkpoint']}`",
        f"- audit/test episodes: {payload['config']['audit_episodes']} / {payload['config']['test_episodes']}",
        f"- test cost mean: {payload['test_summary']['cost_mean']:.4f}",
        f"- test violation rate: {payload['test_summary']['episode_violation_rate']:.4f}",
        "",
        "| cap | audit ep F/Y | test ep F/Y | test block R/Y | issued steps/ep |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in payload["rules"]:
        audit = row["audit"]
        test = row["test"]
        lines.append(
            f"| {row['cap']} | "
            f"{audit['episode_false']:.4f}/{audit['episode_yield']:.4f} | "
            f"{test['episode_false']:.4f}/{test['episode_yield']:.4f} | "
            f"{test['block_risk']:.4f}/{test['block_yield']:.4f} | "
            f"{test['issued_steps_per_episode']:.2f} |"
        )
    output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(cfg: FixedCapAuditConfig) -> Dict:
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
    rules = []
    for cap in caps:
        rules.append(
            {
                "variant": "first_cap",
                "tau": None,
                "cap": int(cap),
                "ucb_valid": False,
                "fixed_rule": True,
                "audit": evaluate_first_cap(audit, int(cap)),
                "test": evaluate_first_cap(test, int(cap)),
            }
        )
    payload = {
        "protocol_version": PROTOCOL_VERSION,
        "scope": "online closed-loop pre-registered first-cap episode audit",
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


def parse_args() -> FixedCapAuditConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--algo", choices=["cpq", "coptidice"], required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--env-id", default=FixedCapAuditConfig.env_id)
    parser.add_argument("--osrl-root", type=Path, default=FixedCapAuditConfig.osrl_root)
    parser.add_argument("--seed", type=int, default=FixedCapAuditConfig.seed)
    parser.add_argument("--audit-episodes", type=int, default=FixedCapAuditConfig.audit_episodes)
    parser.add_argument("--test-episodes", type=int, default=FixedCapAuditConfig.test_episodes)
    parser.add_argument("--max-steps", type=int, default=FixedCapAuditConfig.max_steps)
    parser.add_argument("--cost-limit", type=float, default=FixedCapAuditConfig.cost_limit)
    parser.add_argument("--caps", default=FixedCapAuditConfig.caps)
    parser.add_argument("--device", default=FixedCapAuditConfig.device)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--output", type=Path, default=FixedCapAuditConfig.output)
    args = parser.parse_args()
    return FixedCapAuditConfig(
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
