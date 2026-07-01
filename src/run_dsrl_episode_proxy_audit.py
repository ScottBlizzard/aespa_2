"""Episode-level proxy audit for trained DSRL checkpoint proposers.

This diagnostic keeps the existing offline query-bank contract: actor proposals
are mapped to nearest logged actions, residual labels come from logged H-step
suffix costs, and auditors are selected on independent audit blocks. The new
output groups test query blocks by their logged anchor episode and reports
whether any issued false certificate appears within the sampled episode blocks.

It is not a closed-loop simulator guarantee. It is a bridge diagnostic for
whether action-level selected-risk control survives episode aggregation under
the same official HDF5 residual-label protocol.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from run_dsrl_dataset_pilot import (
    DATA_DIR,
    OUTPUT_DIR,
    ROOT,
    DatasetBank,
    eval_rank,
    eval_reward_bin,
    evaluate_eligible,
    fit_candidate_threshold,
    fit_rank,
    fit_reward_bin,
    fit_selected_rule_family,
    load_logged_dataset,
    one_sided_ucb,
    dataset_path,
    fit_models,
    split_by_episode,
    threshold_grid,
    yield_lcb,
)


def select_best_by_reward(reward: np.ndarray, eligible: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    issued = eligible.any(axis=1)
    masked = np.where(eligible, reward, -np.inf)
    selected = np.argmax(masked, axis=1)
    selected[~issued] = -1
    return issued, selected


def episode_stats_for_mask(data, bank: DatasetBank, eligible: np.ndarray) -> Dict[str, object]:
    issued, selected = select_best_by_reward(bank.reward_scores, eligible)
    rows = np.arange(bank.reward_scores.shape[0])
    chosen = np.where(issued, selected, bank.fallback_index)

    issued_false = np.zeros_like(issued, dtype=bool)
    issued_false[issued] = bank.residual_failure[rows[issued], selected[issued]]
    realized_failure = bank.residual_failure[rows, chosen]
    anchor_episode = data.episode_id[bank.anchor_index]

    unique_episodes = np.unique(anchor_episode)
    any_issued = []
    any_issued_false = []
    any_realized_failure = []
    issued_counts = []
    block_counts = []
    for episode in unique_episodes:
        mask = anchor_episode == episode
        any_issued.append(bool(issued[mask].any()))
        any_issued_false.append(bool(issued_false[mask].any()))
        any_realized_failure.append(bool(realized_failure[mask].any()))
        issued_counts.append(int(issued[mask].sum()))
        block_counts.append(int(mask.sum()))

    any_issued_arr = np.asarray(any_issued, dtype=bool)
    any_issued_false_arr = np.asarray(any_issued_false, dtype=bool)
    any_realized_failure_arr = np.asarray(any_realized_failure, dtype=bool)
    episode_issued = int(any_issued_arr.sum())
    episode_false = int(any_issued_false_arr.sum())
    return {
        "episode_count": int(len(unique_episodes)),
        "episode_claim_yield": float(any_issued_arr.mean()) if len(unique_episodes) else 0.0,
        "episode_false_certification": float(episode_false / episode_issued) if episode_issued else 0.0,
        "episode_realized_failure_rate": float(any_realized_failure_arr.mean()) if len(unique_episodes) else 0.0,
        "episode_issued": episode_issued,
        "episode_failures": episode_false,
        "mean_issued_blocks_per_episode": float(np.mean(issued_counts)) if issued_counts else 0.0,
        "mean_blocks_per_episode": float(np.mean(block_counts)) if block_counts else 0.0,
    }


def fit_episode_rule_family(
    data,
    audit: DatasetBank,
    rules: List[Tuple[float, float]],
    alpha: float,
    gamma: float,
    delta: float,
    use_support: bool,
) -> Dict[str, object] | None:
    candidates: List[Dict[str, object]] = []
    for safety_tau, support_tau in rules:
        eligible = audit.safety_scores <= safety_tau
        if use_support:
            eligible &= audit.support_scores >= support_tau
        stats = episode_stats_for_mask(data, audit, eligible)
        block_eval = evaluate_eligible(audit, eligible, "episode_audit")
        risk_ucb = one_sided_ucb(stats["episode_failures"], stats["episode_issued"], len(rules), delta)
        episode_yield_lcb = yield_lcb(stats["episode_issued"], stats["episode_count"], len(rules), delta)
        if risk_ucb <= alpha and episode_yield_lcb >= gamma:
            candidates.append(
                {
                    "safety_tau": float(safety_tau),
                    "support_tau": float(support_tau),
                    "episode_alpha": float(alpha),
                    "episode_gamma": float(gamma),
                    "audit_episode_risk_ucb": float(risk_ucb),
                    "audit_episode_yield_lcb": float(episode_yield_lcb),
                    "audit_episode_risk": float(stats["episode_false_certification"]),
                    "audit_episode_yield": float(stats["episode_claim_yield"]),
                    "audit_block_risk": float(block_eval.selected_false_certification),
                    "audit_block_yield": float(block_eval.claim_yield),
                    "audit_reward": float(block_eval.normalized_reward),
                    "audit_mean_issued_blocks_per_episode": float(stats["mean_issued_blocks_per_episode"]),
                }
            )
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda item: (
            float(item["audit_reward"]),
            float(item["audit_episode_yield"]),
            float(item["audit_mean_issued_blocks_per_episode"]),
        ),
    )


def cap_eligible_per_episode(data, bank: DatasetBank, eligible: np.ndarray, cap: int) -> np.ndarray:
    if cap <= 0:
        return eligible
    issued, _ = select_best_by_reward(bank.reward_scores, eligible)
    anchor_episode = data.episode_id[bank.anchor_index]
    keep = np.zeros_like(issued, dtype=bool)
    for episode in np.unique(anchor_episode):
        rows = np.flatnonzero((anchor_episode == episode) & issued)
        if rows.size == 0:
            continue
        ordered = rows[np.argsort(bank.anchor_index[rows])]
        keep[ordered[:cap]] = True
    return eligible & keep[:, None]


def method_masks(
    data,
    audit: DatasetBank,
    test: DatasetBank,
    cfg,
    episode_alpha: float,
    episode_gamma: float,
    episode_claim_caps: List[int],
) -> List[Tuple[str, np.ndarray, Dict[str, object] | None]]:
    n, k = test.reward_scores.shape
    masks: List[Tuple[str, np.ndarray, Dict[str, object] | None]] = []
    cap_candidates: List[Tuple[str, np.ndarray, Dict[str, object] | None]] = []
    none_mask = np.ones((n, k), dtype=bool)
    masks.append(("none_original_proposer", none_mask, None))
    cap_candidates.append(("none_original_proposer", none_mask, None))

    safety_thresholds = threshold_grid(audit.safety_scores, 80)
    tau = fit_candidate_threshold(audit, cfg.alpha, cfg.delta, safety_thresholds)
    global_mask = np.zeros((n, k), dtype=bool) if tau is None else (test.safety_scores <= tau)
    global_rule = None if tau is None else {"safety_tau": float(tau)}
    masks.append(("global_candidate_cp", global_mask, global_rule))
    cap_candidates.append(("global_candidate_cp", global_mask, global_rule))

    reward_cert = fit_reward_bin(audit, 20, cfg.alpha, cfg.delta)
    reward_mask = eval_reward_bin(test, reward_cert)
    reward_rule = {"certified_bins": int(reward_cert["certified"].sum())}
    masks.append(("reward_bin_ucb_20", reward_mask, reward_rule))
    cap_candidates.append(("reward_bin_ucb_20", reward_mask, reward_rule))

    rank_cert = fit_rank(audit, cfg.alpha, cfg.delta)
    masks.append(
        (
            "rank_bin_ucb",
            eval_rank(test, rank_cert),
            {
                "certified_ranks": int(rank_cert.sum()),
                "first_certified_rank": int(np.flatnonzero(rank_cert)[0] + 1) if rank_cert.any() else -1,
            },
        )
    )

    crc_rules = [(float(x), 0.0) for x in safety_thresholds]
    crc_rule = fit_selected_rule_family(audit, crc_rules, cfg.alpha, cfg.gamma, cfg.delta, use_support=False)
    crc_mask = np.zeros((n, k), dtype=bool) if crc_rule is None else (test.safety_scores <= crc_rule["safety_tau"])
    masks.append(("crc_style_safety_threshold", crc_mask, crc_rule))
    cap_candidates.append(("crc_style_safety_threshold", crc_mask, crc_rule))

    support_thresholds = np.unique(
        np.concatenate([[0.0], np.quantile(audit.support_scores.reshape(-1), np.linspace(0.10, 0.90, 17))])
    )
    accs_rules = [(float(st), float(su)) for st in safety_thresholds[::2] for su in support_thresholds]
    accs_rule = fit_selected_rule_family(audit, accs_rules, cfg.alpha, cfg.gamma, cfg.delta, use_support=True)
    accs_mask = (
        np.zeros((n, k), dtype=bool)
        if accs_rule is None
        else (test.safety_scores <= accs_rule["safety_tau"]) & (test.support_scores >= accs_rule["support_tau"])
    )
    masks.append(("accs_v0_support_safety", accs_mask, accs_rule))
    cap_candidates.append(("accs_v0_support_safety", accs_mask, accs_rule))

    episode_crc_rule = fit_episode_rule_family(
        data,
        audit,
        crc_rules,
        episode_alpha,
        episode_gamma,
        cfg.delta,
        use_support=False,
    )
    episode_crc_mask = (
        np.zeros((n, k), dtype=bool)
        if episode_crc_rule is None
        else (test.safety_scores <= episode_crc_rule["safety_tau"])
    )
    masks.append(("episode_crc_safety_threshold", episode_crc_mask, episode_crc_rule))

    episode_accs_rule = fit_episode_rule_family(
        data,
        audit,
        accs_rules,
        episode_alpha,
        episode_gamma,
        cfg.delta,
        use_support=True,
    )
    episode_accs_mask = (
        np.zeros((n, k), dtype=bool)
        if episode_accs_rule is None
        else (test.safety_scores <= episode_accs_rule["safety_tau"])
        & (test.support_scores >= episode_accs_rule["support_tau"])
    )
    masks.append(("episode_accs_support_safety", episode_accs_mask, episode_accs_rule))

    for episode_claim_cap in episode_claim_caps:
        if episode_claim_cap <= 0:
            continue
        for base_name, base_mask, base_rule in cap_candidates:
            capped_rule = {"episode_claim_cap": int(episode_claim_cap)}
            if base_rule is not None:
                capped_rule.update(base_rule)
            masks.append(
                (
                    f"{base_name}_episode_cap{episode_claim_cap}",
                    cap_eligible_per_episode(data, test, base_mask, episode_claim_cap),
                    capped_rule,
                )
            )

    masks.append(("oracle_residual_label", test.residual_failure == 0, None))
    return masks


def episode_proxy_for_mask(data, test: DatasetBank, eligible: np.ndarray, name: str, selected_rule) -> Dict[str, object]:
    action_metric = evaluate_eligible(test, eligible, name, selected_rule)
    stats = episode_stats_for_mask(data, test, eligible)
    return {
        "name": name,
        "block_selected_false_certification": action_metric.selected_false_certification,
        "block_claim_yield": action_metric.claim_yield,
        "block_realized_failure_rate": action_metric.episode_violation_rate,
        "block_issued": action_metric.issued,
        "block_failures": action_metric.failures,
        **stats,
        "selected_rule": selected_rule,
    }


def make_report(payload: Dict[str, object], out_md: Path) -> None:
    lines = [
        f"# Episode Proxy Audit: {payload['algo']} {payload['env']}",
        "",
        "This is a logged episode-block proxy, not a closed-loop simulator guarantee.",
        "",
        f"- checkpoint: `{payload['checkpoint']}`",
        f"- residual budget: {payload['residual_budget']:.6f}",
        f"- test episodes: {payload['query_bank']['test_episode_count']}",
        f"- test blocks: {payload['query_bank']['n_test_blocks']}",
        "",
        "| method | block R/Y | episode false/yield | realized episode fail | issued episodes |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in payload["episode_proxy"]:
        lines.append(
            "| {name} | {br:.2f} / {by:.2f} | {er:.2f} / {ey:.2f} | {rf:.2f} | {ei}/{ec} |".format(
                name=row["name"],
                br=100.0 * row["block_selected_false_certification"],
                by=100.0 * row["block_claim_yield"],
                er=100.0 * row["episode_false_certification"],
                ey=100.0 * row["episode_claim_yield"],
                rf=100.0 * row["episode_realized_failure_rate"],
                ei=row["episode_issued"],
                ec=row["episode_count"],
            )
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algo", choices=["cpq", "coptidice"], required=True)
    parser.add_argument("--env-id", default="OfflineCarCircle-v0")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260624)
    parser.add_argument("--risk-quantile", type=float, default=0.92)
    parser.add_argument("--horizon", type=int, default=40)
    parser.add_argument("--k", type=int, default=64)
    parser.add_argument("--proposal-samples", type=int, default=96)
    parser.add_argument("--n-audit", type=int, default=9000)
    parser.add_argument("--n-test", type=int, default=12000)
    parser.add_argument("--neighbor-pool", type=int, default=512)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--batch-size-eval", type=int, default=8192)
    parser.add_argument("--episode-len", type=int, default=300)
    parser.add_argument("--episode-alpha", type=float, default=0.05)
    parser.add_argument("--episode-gamma", type=float, default=0.25)
    parser.add_argument("--episode-claim-cap", type=int, default=0)
    parser.add_argument(
        "--episode-claim-caps",
        default="",
        help="Comma-separated cap values; overrides --episode-claim-cap when nonempty.",
    )
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    return parser.parse_args()


def run(args: argparse.Namespace) -> Dict[str, object]:
    if args.algo == "cpq":
        from run_dsrl_cpq_checkpoint_pilot import CPQCheckpointConfig, build_cpq_bank, load_cpq_model

        cfg = CPQCheckpointConfig(
            seed=args.seed,
            env_id=args.env_id,
            checkpoint=args.checkpoint,
            k=args.k,
            proposal_samples=args.proposal_samples,
            n_audit=args.n_audit,
            n_test=args.n_test,
            horizon=args.horizon,
            neighbor_pool=args.neighbor_pool,
            risk_quantile=args.risk_quantile,
            device=args.device,
            batch_size_eval=args.batch_size_eval,
            episode_len=args.episode_len,
            save_query_bank=False,
        )
        build_bank = build_cpq_bank
        load_model = load_cpq_model
    else:
        from run_dsrl_coptidice_checkpoint_pilot import (
            COptiDICECheckpointConfig,
            build_coptidice_bank,
            load_coptidice_model,
        )

        cfg = COptiDICECheckpointConfig(
            seed=args.seed,
            env_id=args.env_id,
            checkpoint=args.checkpoint,
            k=args.k,
            proposal_samples=args.proposal_samples,
            n_audit=args.n_audit,
            n_test=args.n_test,
            horizon=args.horizon,
            neighbor_pool=args.neighbor_pool,
            risk_quantile=args.risk_quantile,
            device=args.device,
            batch_size_eval=args.batch_size_eval,
            episode_len=args.episode_len,
            save_query_bank=False,
        )
        build_bank = build_coptidice_bank
        load_model = load_coptidice_model

    path = dataset_path(cfg.env_id, DATA_DIR)
    data = load_logged_dataset(path, cfg.horizon)
    splits = split_by_episode(data, cfg.seed)
    scaler, reward_model, cost_model = fit_models(data, splits["train"], cfg.seed)
    residual_budget = float(np.quantile(data.residual_cost[splits["tune"]], cfg.risk_quantile))
    model, device, checkpoint = load_model(data, cfg)

    audit, audit_diag = build_bank(
        data,
        splits["audit"],
        splits["audit"],
        cfg.n_audit,
        residual_budget,
        cfg.seed + 10,
        scaler,
        reward_model,
        cost_model,
        model,
        device,
        cfg,
    )
    test, test_diag = build_bank(
        data,
        splits["test"],
        splits["test"],
        cfg.n_test,
        residual_budget,
        cfg.seed + 20,
        scaler,
        reward_model,
        cost_model,
        model,
        device,
        cfg,
    )

    if args.episode_claim_caps.strip():
        episode_claim_caps = [int(item) for item in args.episode_claim_caps.split(",") if item.strip()]
    else:
        episode_claim_caps = [int(args.episode_claim_cap)] if int(args.episode_claim_cap) > 0 else []

    masks = method_masks(data, audit, test, cfg, args.episode_alpha, args.episode_gamma, episode_claim_caps)
    episode_rows = [episode_proxy_for_mask(data, test, eligible, name, rule) for name, eligible, rule in masks]
    payload: Dict[str, object] = {
        "protocol_version": "episode-proxy-2026-06-24",
        "algo": args.algo,
        "env": cfg.env_id,
        "dataset_file": str(path.relative_to(ROOT)),
        "checkpoint": str(checkpoint.relative_to(ROOT)) if checkpoint.is_relative_to(ROOT) else str(checkpoint),
        "residual_budget": residual_budget,
        "episode_proxy_protocol": (
            "test query blocks grouped by logged anchor episode; episode false certification is "
            "the fraction of episodes with at least one issued false residual-cost claim among "
            "episodes with at least one issued claim"
        ),
        "episode_allocation_config": {
            "episode_alpha": float(args.episode_alpha),
            "episode_gamma": float(args.episode_gamma),
            "episode_claim_caps": [int(cap) for cap in episode_claim_caps],
            "episode_rule_fit": "audit episodes; risk UCB over issued episodes; yield LCB over all audit episodes",
        },
        "query_bank": {
            "n_audit_blocks": int(audit.reward_scores.shape[0]),
            "n_test_blocks": int(test.reward_scores.shape[0]),
            "test_episode_count": int(np.unique(data.episode_id[test.anchor_index]).size),
            "k": cfg.k,
            "neighbor_pool": cfg.neighbor_pool,
            "seed": cfg.seed,
        },
        "diagnostics": {
            "audit": audit_diag,
            "test": test_diag,
            "test_candidate_false_rate": float(test.residual_failure.mean()),
            "test_top_reward_false_rate": float(
                test.residual_failure[np.arange(test.reward_scores.shape[0]), test.reward_scores.argmax(axis=1)].mean()
            ),
        },
        "config": {key: str(value) if isinstance(value, Path) else value for key, value in asdict(cfg).items()},
        "episode_proxy": episode_rows,
    }
    return payload


def main() -> None:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"phase_dsrl_episode_proxy_{args.algo}_{args.env_id}_seed{args.seed}"
    out_json = args.out_json or (OUTPUT_DIR / f"{stem}_server.json")
    out_md = args.out_md or (OUTPUT_DIR / f"{stem}_server.md")
    payload = run(args)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    make_report(payload, out_md)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
