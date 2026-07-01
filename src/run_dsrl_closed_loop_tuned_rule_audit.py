"""Closed-loop tune/audit/test episode-rule frontier.

This diagnostic uses three independent online splits. The tune split selects a
small pre-declared certificate-emission rule. The selected rule is then frozen
before audit/test episodes are evaluated, so audit/test episode false rates can
be reported with ordinary exact binomial intervals for the frozen rule.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

from run_dsrl_closed_loop_audit import (
    OUTPUT_DIR,
    ROOT,
    load_model,
    parse_caps,
    reset_env,
    resolve_path,
    rollout_split,
    serialize_config,
    summarize_rollouts,
    make_env,
)


PROTOCOL_VERSION = "2026-06-30-closed-loop-tuned-rule-v1"


@dataclass(frozen=True)
class TunedRuleAuditConfig:
    algo: str
    checkpoint: Path
    env_id: str = "OfflineCarCircle-v0"
    osrl_root: Path = ROOT / "external" / "OSRL"
    seed: int = 20260624
    tune_episodes: int = 100
    audit_episodes: int = 200
    test_episodes: int = 200
    max_steps: int = 300
    cost_limit: float = 20.0
    caps: str = "16,32,64,128,256,512"
    windows: str = "all,early,mid"
    score_quantiles: str = "0.05,0.10,0.20,0.35,0.50,0.65,0.80"
    alpha_ep: float = 0.05
    min_episode_yield: float = 0.10
    device: str = "cuda:0"
    deterministic: bool = True
    output: Path = OUTPUT_DIR / "phase_dsrl_closed_loop_tuned_rule_audit.json"


def parse_csv_floats(text: str) -> List[float]:
    values = [float(x.strip()) for x in text.split(",") if x.strip()]
    if not values:
        raise ValueError("At least one float value is required")
    return sorted(set(values))


def parse_csv_text(text: str) -> List[str]:
    values = [x.strip() for x in text.split(",") if x.strip()]
    if not values:
        raise ValueError("At least one text value is required")
    return list(dict.fromkeys(values))


def transformed_values(scores: Iterable[float], variant: str) -> np.ndarray:
    values = np.asarray(list(scores), dtype=np.float64)
    if variant == "score":
        return values
    if variant == "neg_score":
        return -values
    raise ValueError(f"Unsupported variant: {variant}")


def window_bounds(window: str, max_steps: int) -> Tuple[int, int]:
    if window == "all":
        return 0, int(max_steps)
    if window == "early":
        return 0, max(1, int(round(0.25 * max_steps)))
    if window == "mid":
        return int(round(0.25 * max_steps)), int(round(0.50 * max_steps))
    if window == "late":
        return int(round(0.50 * max_steps)), int(max_steps)
    raise ValueError(f"Unsupported window: {window}")


def window_mask(length: int, window: str, max_steps: int) -> np.ndarray:
    mask = np.zeros(int(length), dtype=bool)
    start, end = window_bounds(window, max_steps)
    start = max(0, min(start, int(length)))
    end = max(start, min(end, int(length)))
    mask[start:end] = True
    return mask


def candidate_thresholds(episodes: List[Dict], variant: str, quantiles: List[float]) -> List[float]:
    all_scores = np.concatenate([transformed_values(ep["scores"], variant) for ep in episodes if ep["scores"]])
    if all_scores.size == 0:
        return []
    qs = np.asarray(quantiles, dtype=np.float64)
    qs = np.clip(qs, 0.0, 1.0)
    return [float(x) for x in np.unique(np.quantile(all_scores, qs))]


def eligible_for_rule(ep: Dict, rule: Dict, max_steps: int) -> np.ndarray:
    length = int(ep["length"])
    if rule["rule_type"] == "first_cap":
        out = np.zeros(length, dtype=bool)
        out[: min(int(rule["cap"]), length)] = True
        return out

    if rule["rule_type"] != "score_gate":
        raise ValueError(f"Unsupported rule type: {rule['rule_type']}")

    values = transformed_values(ep["scores"], str(rule["variant"]))
    eligible = window_mask(length, str(rule["window"]), max_steps)
    eligible &= values <= float(rule["tau"])
    cap = int(rule["cap"])
    if cap > 0 and int(eligible.sum()) > cap:
        keep = np.flatnonzero(eligible)[:cap]
        capped = np.zeros_like(eligible, dtype=bool)
        capped[keep] = True
        eligible = capped
    return eligible


def evaluate_rule(episodes: List[Dict], rule: Dict, max_steps: int) -> Dict[str, float]:
    total_steps = int(sum(ep["length"] for ep in episodes))
    issued_steps = 0
    false_steps = 0
    issued_episodes = 0
    false_episodes = 0
    for ep in episodes:
        issued = eligible_for_rule(ep, rule, max_steps)
        count = int(issued.sum())
        issued_steps += count
        if count:
            issued_episodes += 1
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


def build_rule_family(cfg: TunedRuleAuditConfig, tune: List[Dict]) -> List[Dict]:
    caps = parse_caps(cfg.caps)
    windows = parse_csv_text(cfg.windows)
    quantiles = parse_csv_floats(cfg.score_quantiles)
    variants = ["score"] if cfg.algo == "cpq" else ["score", "neg_score"]

    rules: List[Dict] = []
    for cap in caps:
        rules.append(
            {
                "rule_type": "first_cap",
                "variant": "none",
                "window": "prefix",
                "tau": None,
                "cap": int(cap),
            }
        )

    for variant in variants:
        for tau in candidate_thresholds(tune, variant, quantiles):
            for window in windows:
                for cap in caps:
                    rules.append(
                        {
                            "rule_type": "score_gate",
                            "variant": variant,
                            "window": window,
                            "tau": float(tau),
                            "cap": int(cap),
                        }
                    )
    return rules


def select_rule(cfg: TunedRuleAuditConfig, tune: List[Dict], rules: List[Dict]) -> Dict:
    evaluated = []
    for index, rule in enumerate(rules):
        metrics = evaluate_rule(tune, rule, cfg.max_steps)
        evaluated.append(
            {
                "rule_index": int(index),
                **rule,
                "tune": metrics,
                "tune_empirical_valid": bool(
                    metrics["episode_false"] <= cfg.alpha_ep
                    and metrics["episode_yield"] >= cfg.min_episode_yield
                    and metrics["issued_episodes"] > 0
                ),
            }
        )

    valid = [item for item in evaluated if item["tune_empirical_valid"]]
    if valid:
        selected = max(
            valid,
            key=lambda item: (
                item["tune"]["issued_steps_per_episode"],
                item["tune"]["episode_yield"],
                -item["tune"]["episode_false"],
                -item["rule_index"],
            ),
        )
        return {**selected, "selection_reason": "tune_empirical_alpha_yield_valid"}

    fallback_pool = [item for item in evaluated if item["tune"]["issued_episodes"] > 0]
    if not fallback_pool:
        fallback_pool = evaluated
    selected = max(
        fallback_pool,
        key=lambda item: (
            -item["tune"]["episode_false"],
            item["tune"]["episode_yield"],
            item["tune"]["issued_steps_per_episode"],
            -item["rule_index"],
        ),
    )
    return {**selected, "selection_reason": "diagnostic_best_tune_tradeoff_no_valid_rule"}


def compact_top_candidates(candidates: List[Dict], limit: int = 20) -> List[Dict]:
    ordered = sorted(
        candidates,
        key=lambda item: (
            int(item["tune_empirical_valid"]),
            int(item["tune"]["issued_episodes"] > 0),
            -item["tune"]["episode_false"],
            item["tune"]["issued_steps_per_episode"],
            item["tune"]["episode_yield"],
        ),
        reverse=True,
    )
    return ordered[:limit]


def write_outputs(payload: Dict, output: Path) -> None:
    output = resolve_path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    rule = payload["selected_rule"]
    lines = [
        "# Closed-Loop Tuned-Rule Episode Audit",
        "",
        "The rule family is selected only on the tune split and then frozen before audit/test reporting.",
        "",
        f"- algo: {payload['config']['algo']}",
        f"- env: {payload['config']['env_id']}",
        f"- checkpoint: `{payload['checkpoint']}`",
        f"- tune/audit/test episodes: {payload['config']['tune_episodes']} / {payload['config']['audit_episodes']} / {payload['config']['test_episodes']}",
        f"- selected rule: {rule['rule_type']} variant={rule['variant']} window={rule['window']} cap={rule['cap']} tau={rule['tau']}",
        f"- selection reason: {rule['selection_reason']}",
        f"- test cost mean: {payload['test_summary']['cost_mean']:.4f}",
        f"- test violation rate: {payload['test_summary']['episode_violation_rate']:.4f}",
        "",
        "| split | ep F/Y | block R/Y | issued steps/ep | false/issued ep |",
        "|---|---:|---:|---:|---:|",
    ]
    for split in ["tune", "audit", "test"]:
        metrics = rule[split]
        lines.append(
            f"| {split} | "
            f"{metrics['episode_false']:.4f}/{metrics['episode_yield']:.4f} | "
            f"{metrics['block_risk']:.4f}/{metrics['block_yield']:.4f} | "
            f"{metrics['issued_steps_per_episode']:.2f} | "
            f"{metrics['false_episodes']}/{metrics['issued_episodes']} |"
        )
    output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(cfg: TunedRuleAuditConfig) -> Dict:
    env = make_env(cfg.env_id, cfg.cost_limit)
    obs0 = reset_env(env, cfg.seed)
    model, device, checkpoint = load_model(
        cfg,
        obs_dim=int(obs0.shape[0]),
        action_dim=int(env.action_space.shape[0]),
    )
    tune = rollout_split(env, model, cfg, device, cfg.seed + 5_000, cfg.tune_episodes)
    audit = rollout_split(env, model, cfg, device, cfg.seed + 10_000, cfg.audit_episodes)
    test = rollout_split(env, model, cfg, device, cfg.seed + 20_000, cfg.test_episodes)

    rules = build_rule_family(cfg, tune)
    selected = select_rule(cfg, tune, rules)
    selected_rule = {
        **selected,
        "audit": evaluate_rule(audit, selected, cfg.max_steps),
        "test": evaluate_rule(test, selected, cfg.max_steps),
    }

    payload = {
        "protocol_version": PROTOCOL_VERSION,
        "scope": "online closed-loop tune-selected frozen episode rule",
        "config": {
            **serialize_config(cfg),
            "checkpoint": str(resolve_path(cfg.checkpoint)),
            "output": str(resolve_path(cfg.output)),
        },
        "checkpoint": str(checkpoint),
        "device": str(device),
        "n_candidate_rules": int(len(rules)),
        "top_tune_candidates": compact_top_candidates(
            [
                {
                    "rule_index": int(index),
                    **rule,
                    "tune": evaluate_rule(tune, rule, cfg.max_steps),
                    "tune_empirical_valid": bool(
                        evaluate_rule(tune, rule, cfg.max_steps)["episode_false"] <= cfg.alpha_ep
                        and evaluate_rule(tune, rule, cfg.max_steps)["episode_yield"] >= cfg.min_episode_yield
                        and evaluate_rule(tune, rule, cfg.max_steps)["issued_episodes"] > 0
                    ),
                }
                for index, rule in enumerate(rules)
            ]
        ),
        "selected_rule": selected_rule,
        "tune_summary": summarize_rollouts(env, tune, cfg.cost_limit),
        "audit_summary": summarize_rollouts(env, audit, cfg.cost_limit),
        "test_summary": summarize_rollouts(env, test, cfg.cost_limit),
    }
    env.close()
    write_outputs(payload, cfg.output)
    return payload


def parse_args() -> TunedRuleAuditConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--algo", choices=["cpq", "coptidice"], required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--env-id", default=TunedRuleAuditConfig.env_id)
    parser.add_argument("--osrl-root", type=Path, default=TunedRuleAuditConfig.osrl_root)
    parser.add_argument("--seed", type=int, default=TunedRuleAuditConfig.seed)
    parser.add_argument("--tune-episodes", type=int, default=TunedRuleAuditConfig.tune_episodes)
    parser.add_argument("--audit-episodes", type=int, default=TunedRuleAuditConfig.audit_episodes)
    parser.add_argument("--test-episodes", type=int, default=TunedRuleAuditConfig.test_episodes)
    parser.add_argument("--max-steps", type=int, default=TunedRuleAuditConfig.max_steps)
    parser.add_argument("--cost-limit", type=float, default=TunedRuleAuditConfig.cost_limit)
    parser.add_argument("--caps", default=TunedRuleAuditConfig.caps)
    parser.add_argument("--windows", default=TunedRuleAuditConfig.windows)
    parser.add_argument("--score-quantiles", default=TunedRuleAuditConfig.score_quantiles)
    parser.add_argument("--alpha-ep", type=float, default=TunedRuleAuditConfig.alpha_ep)
    parser.add_argument("--min-episode-yield", type=float, default=TunedRuleAuditConfig.min_episode_yield)
    parser.add_argument("--device", default=TunedRuleAuditConfig.device)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--output", type=Path, default=TunedRuleAuditConfig.output)
    args = parser.parse_args()
    return TunedRuleAuditConfig(
        algo=args.algo,
        checkpoint=args.checkpoint,
        env_id=args.env_id,
        osrl_root=args.osrl_root,
        seed=args.seed,
        tune_episodes=args.tune_episodes,
        audit_episodes=args.audit_episodes,
        test_episodes=args.test_episodes,
        max_steps=args.max_steps,
        cost_limit=args.cost_limit,
        caps=args.caps,
        windows=args.windows,
        score_quantiles=args.score_quantiles,
        alpha_ep=args.alpha_ep,
        min_episode_yield=args.min_episode_yield,
        device=args.device,
        deterministic=not args.stochastic,
        output=args.output,
    )


def main() -> None:
    payload = run(parse_args())
    print(json.dumps({"selected_rule": payload["selected_rule"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    if str(Path(__file__).resolve().parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
