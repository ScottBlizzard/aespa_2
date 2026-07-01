"""Hardened baselines for the selection-amplification toy.

This script adds stronger local baselines:

- selected-block accept-or-abstain;
- reward-bin UCB certifiers;
- rank-bin UCB certifier;
- CRC-style threshold auditor;
- ACCS-v0 finite-rule auditor;
- sensitivity sweeps over audit size, gamma, and delta.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eval_metrics import closed_form_selection_risk, summarize_issued_claims
from selective_auditor import (
    audit_threshold_family,
    evaluate_abstain_all,
    evaluate_accept_all,
    evaluate_threshold_rule,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
FIGURE_DIR = ROOT / "figures"


def one_sided_ucb(successes: int, n: int, n_rules: int, delta: float) -> float:
    """Simple Hoeffding UCB for a Bernoulli risk."""

    if n <= 0:
        return float("inf")
    phat = successes / n
    eps = np.sqrt(np.log(2.0 * max(n_rules, 1) / delta) / (2.0 * n))
    return float(min(1.0, phat + eps))


def add_row(rows, k, method, evaluated, proposal_false_rate, extra=None):
    summary = evaluated["summary"]
    row = {
        "k": k,
        "method": method,
        "proposal_false_rate": proposal_false_rate,
        "issued": summary.issued,
        "claim_yield": summary.claim_yield,
        "selected_false_certification": summary.selective_risk,
        "mean_reward": summary.mean_reward,
        "mean_reward_issued": summary.mean_reward_issued,
        "fallback_rate": summary.fallback_rate,
    }
    if extra:
        row.update(extra)
    rows.append(row)


def summarize_selected_x(selected_x: np.ndarray, issued: np.ndarray, violation_threshold: float) -> dict:
    selected_x = np.asarray(selected_x, dtype=float)
    issued = np.asarray(issued, dtype=bool)
    failure = issued & (selected_x > violation_threshold)
    return {
        "issued": issued,
        "failure": failure,
        "reward": selected_x,
        "summary": summarize_issued_claims(issued, failure, selected_x),
    }


def fit_reward_bin_certifier(
    audit_blocks: np.ndarray,
    n_bins: int,
    alpha: float,
    delta: float,
    violation_threshold: float,
) -> Dict[str, np.ndarray]:
    """Fit a reward-conditioned candidate certifier using individual candidates."""

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    x = audit_blocks.reshape(-1)
    bin_id = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, n_bins - 1)
    certified = np.zeros(n_bins, dtype=bool)
    risk_ucb = np.full(n_bins, np.inf, dtype=float)
    counts = np.zeros(n_bins, dtype=int)
    failures = np.zeros(n_bins, dtype=int)
    for idx in range(n_bins):
        mask = bin_id == idx
        counts[idx] = int(mask.sum())
        failures[idx] = int((x[mask] > violation_threshold).sum())
        risk_ucb[idx] = one_sided_ucb(failures[idx], counts[idx], n_bins, delta)
        certified[idx] = risk_ucb[idx] <= alpha
    return {
        "edges": edges,
        "certified": certified,
        "risk_ucb": risk_ucb,
        "counts": counts,
        "failures": failures,
    }


def evaluate_reward_bin_certifier(
    x_blocks: np.ndarray,
    certifier: Dict[str, np.ndarray],
    violation_threshold: float,
) -> dict:
    edges = certifier["edges"]
    certified = certifier["certified"]
    n_bins = len(certified)
    bin_id = np.clip(np.searchsorted(edges, x_blocks, side="right") - 1, 0, n_bins - 1)
    eligible = certified[bin_id]
    issued = eligible.any(axis=1)
    selected_x = np.zeros(x_blocks.shape[0], dtype=float)
    if issued.any():
        masked = np.where(eligible, x_blocks, -np.inf)
        selected_x[issued] = masked[issued].max(axis=1)
    return summarize_selected_x(selected_x, issued, violation_threshold)


def fit_rank_bin_certifier(
    audit_blocks: np.ndarray,
    alpha: float,
    delta: float,
    violation_threshold: float,
) -> Dict[str, np.ndarray]:
    """Fit a rank-conditioned certifier over sorted candidate ranks."""

    ranked = np.sort(audit_blocks, axis=1)[:, ::-1]
    n_blocks, k = ranked.shape
    failures = (ranked > violation_threshold).sum(axis=0).astype(int)
    risk_ucb = np.array([one_sided_ucb(int(f), n_blocks, k, delta) for f in failures])
    certified = risk_ucb <= alpha
    return {
        "certified": certified,
        "risk_ucb": risk_ucb,
        "failures": failures,
    }


def evaluate_rank_bin_certifier(
    x_blocks: np.ndarray,
    certifier: Dict[str, np.ndarray],
    violation_threshold: float,
) -> dict:
    ranked = np.sort(x_blocks, axis=1)[:, ::-1]
    certified = certifier["certified"]
    issued = np.repeat(bool(certified.any()), ranked.shape[0])
    selected_x = np.zeros(ranked.shape[0], dtype=float)
    if certified.any():
        first_certified_rank = int(np.flatnonzero(certified)[0])
        selected_x[:] = ranked[:, first_certified_rank]
    return summarize_selected_x(selected_x, issued, violation_threshold)


def evaluate_selected_block_accept_or_abstain(
    audit_blocks: np.ndarray,
    test_blocks: np.ndarray,
    alpha: float,
    delta: float,
    violation_threshold: float,
) -> Tuple[dict, Dict[str, float]]:
    """Selected-block baseline: detect accept-all risk, then accept all or abstain."""

    audit_selected = audit_blocks.max(axis=1)
    failures = int((audit_selected > violation_threshold).sum())
    risk_ucb = one_sided_ucb(failures, audit_blocks.shape[0], 1, delta)
    if risk_ucb <= alpha:
        evaluated = evaluate_accept_all(test_blocks, violation_threshold)
        mode = "accept_all"
    else:
        evaluated = evaluate_abstain_all(test_blocks)
        mode = "abstain_all"
    return evaluated, {
        "selected_block_audit_failures": failures,
        "selected_block_risk_ucb": risk_ucb,
        "selected_block_mode": mode,
    }


def audit_threshold_family_crc_style(
    audit_blocks: np.ndarray,
    thresholds: Iterable[float],
    alpha: float,
    gamma: float,
    delta: float,
    violation_threshold: float,
) -> Dict[str, float]:
    """CRC-style threshold selector with direct conditional-risk UCB."""

    thresholds = sorted(float(t) for t in thresholds)
    candidates = []
    for tau in thresholds:
        evaluated = evaluate_threshold_rule(audit_blocks, tau, violation_threshold)
        summary = evaluated["summary"]
        risk_ucb = one_sided_ucb(summary.failures, summary.issued, len(thresholds), delta)
        yield_lcb = max(
            0.0,
            summary.claim_yield
            - np.sqrt(np.log(2.0 * len(thresholds) / delta) / (2.0 * summary.n_blocks)),
        )
        feasible = risk_ucb <= alpha and yield_lcb >= gamma
        candidates.append(
            {
                "tau": tau,
                "risk_ucb": risk_ucb,
                "yield_lcb": yield_lcb,
                "mean_reward": summary.mean_reward,
                "feasible": feasible,
            }
        )
    feasible = [item for item in candidates if item["feasible"]]
    selected = max(feasible, key=lambda item: (item["mean_reward"], item["tau"])) if feasible else None
    return {
        "selected_tau": np.nan if selected is None else selected["tau"],
        "selected": selected,
        "feasible_count": len(feasible),
    }


def run_hardened_experiment(
    seed: int = 20260626,
    n_test: int = 200_000,
    n_audit: int = 50_000,
    alpha: float = 0.05,
    gamma: float = 0.70,
    delta: float = 0.05,
    violation_threshold: float = 0.96,
):
    rng = np.random.default_rng(seed)
    ks = [1, 2, 4, 8, 16, 32]
    thresholds = np.unique(np.concatenate([np.linspace(0.70, 1.0, 301), [violation_threshold]]))
    rows = []
    selected_rules = {}

    for k in ks:
        x_test = rng.uniform(0.0, 1.0, size=(n_test, k))
        x_audit = rng.uniform(0.0, 1.0, size=(n_audit, k))
        exact_risk = closed_form_selection_risk(1.0 - violation_threshold, k)

        add_row(
            rows,
            k,
            "global_cp_marginal",
            evaluate_accept_all(x_test, violation_threshold),
            proposal_false_rate=1.0 - violation_threshold,
            extra={"closed_form_selected_risk": exact_risk},
        )
        add_row(
            rows,
            k,
            "group_cp_irrelevant_groups",
            evaluate_accept_all(x_test, violation_threshold),
            proposal_false_rate=1.0 - violation_threshold,
            extra={"closed_form_selected_risk": exact_risk},
        )

        selected_block, selected_block_extra = evaluate_selected_block_accept_or_abstain(
            x_audit, x_test, alpha, delta, violation_threshold
        )
        add_row(
            rows,
            k,
            "selected_block_accept_or_abstain",
            selected_block,
            proposal_false_rate=np.nan,
            extra=selected_block_extra,
        )

        for n_bins in [20, 50]:
            certifier = fit_reward_bin_certifier(
                x_audit,
                n_bins=n_bins,
                alpha=alpha,
                delta=delta,
                violation_threshold=violation_threshold,
            )
            evaluated = evaluate_reward_bin_certifier(x_test, certifier, violation_threshold)
            add_row(
                rows,
                k,
                f"reward_bin_ucb_{n_bins}",
                evaluated,
                proposal_false_rate=np.nan,
                extra={
                    "n_bins": n_bins,
                    "certified_bins": int(certifier["certified"].sum()),
                    "max_certified_edge": float(
                        certifier["edges"][np.flatnonzero(certifier["certified"])[-1] + 1]
                    )
                    if certifier["certified"].any()
                    else np.nan,
                },
            )

        rank_certifier = fit_rank_bin_certifier(x_audit, alpha, delta, violation_threshold)
        evaluated_rank = evaluate_rank_bin_certifier(x_test, rank_certifier, violation_threshold)
        add_row(
            rows,
            k,
            "rank_bin_ucb",
            evaluated_rank,
            proposal_false_rate=np.nan,
            extra={
                "certified_ranks": int(rank_certifier["certified"].sum()),
                "first_certified_rank": int(np.flatnonzero(rank_certifier["certified"])[0] + 1)
                if rank_certifier["certified"].any()
                else np.nan,
            },
        )

        if 1.0 - violation_threshold <= alpha / k:
            bonferroni = evaluate_accept_all(x_test, violation_threshold)
            note = "accept_all"
        else:
            bonferroni = evaluate_abstain_all(x_test)
            note = "abstain_all_binary_residual"
        add_row(
            rows,
            k,
            "bonferroni_alpha_over_k",
            bonferroni,
            proposal_false_rate=1.0 - violation_threshold,
            extra={"note": note},
        )

        crc_selected = audit_threshold_family_crc_style(
            x_audit,
            thresholds=thresholds,
            alpha=alpha,
            gamma=gamma,
            delta=delta,
            violation_threshold=violation_threshold,
        )
        if np.isnan(crc_selected["selected_tau"]):
            crc_eval = evaluate_abstain_all(x_test)
        else:
            crc_eval = evaluate_threshold_rule(
                x_test,
                tau=crc_selected["selected_tau"],
                violation_threshold=violation_threshold,
            )
        add_row(
            rows,
            k,
            "crc_style_threshold_auditor",
            crc_eval,
            proposal_false_rate=np.nan,
            extra={
                "tau": crc_selected["selected_tau"],
                "crc_feasible_count": crc_selected["feasible_count"],
                "crc_risk_ucb": np.nan
                if crc_selected["selected"] is None
                else crc_selected["selected"]["risk_ucb"],
                "crc_yield_lcb": np.nan
                if crc_selected["selected"] is None
                else crc_selected["selected"]["yield_lcb"],
            },
        )

        selected = audit_threshold_family(
            x_audit,
            thresholds=thresholds,
            violation_threshold=violation_threshold,
            alpha=alpha,
            gamma=gamma,
            delta=delta,
        )
        selected_rules[str(k)] = {
            "epsilon": selected.epsilon,
            "n_rules": selected.n_rules,
            "selected_tau": selected.selected_tau,
            "selected": None if selected.selected is None else selected.selected.to_dict(),
            "feasible_count": sum(1 for rule in selected.rules if rule.feasible),
        }
        if selected.selected_tau is None:
            accs = evaluate_abstain_all(x_test)
            accs_extra = {"tau": np.nan, "audit_risk_ucb": np.nan, "audit_yield_lcb": np.nan}
        else:
            accs = evaluate_threshold_rule(x_test, selected.selected_tau, violation_threshold)
            accs_extra = {
                "tau": selected.selected_tau,
                "audit_risk_ucb": selected.selected.risk_ucb,
                "audit_yield_lcb": selected.selected.yield_lcb,
            }
        add_row(
            rows,
            k,
            "accs_v0_finite_rule_auditor",
            accs,
            proposal_false_rate=np.nan,
            extra=accs_extra,
        )

        oracle = evaluate_threshold_rule(x_test, violation_threshold, violation_threshold)
        add_row(
            rows,
            k,
            "oracle_tau_0_96",
            oracle,
            proposal_false_rate=0.0,
            extra={"tau": violation_threshold},
        )

    df = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / "toy_selection_failure_hardened.csv"
    summary = OUTPUT_DIR / "toy_selection_failure_hardened_summary.json"
    df.to_csv(out, index=False)
    summary.write_text(
        json.dumps(
            {
                "seed": seed,
                "n_test": n_test,
                "n_audit": n_audit,
                "alpha": alpha,
                "gamma": gamma,
                "delta": delta,
                "violation_threshold": violation_threshold,
                "selected_rules": selected_rules,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    plot_hardened(df)
    sensitivity = run_sensitivity(seed + 1, violation_threshold, alpha)
    return df, sensitivity


def run_sensitivity(
    seed: int,
    violation_threshold: float,
    alpha: float,
    n_test: int = 50_000,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    k = 16
    test_blocks = rng.uniform(0.0, 1.0, size=(n_test, k))
    thresholds = np.unique(np.concatenate([np.linspace(0.72, 1.0, 141), [violation_threshold]]))
    configs = []
    for n_audit in [500, 1_000, 5_000, 10_000, 50_000]:
        configs.append({"sweep": "n_audit", "n_audit": n_audit, "gamma": 0.70, "delta": 0.05})
    for gamma in [0.50, 0.70, 0.90]:
        configs.append({"sweep": "gamma", "n_audit": 5_000, "gamma": gamma, "delta": 0.05})
    for delta in [0.10, 0.05, 0.01]:
        configs.append({"sweep": "delta", "n_audit": 5_000, "gamma": 0.70, "delta": delta})

    rows = []
    for cfg_id, cfg in enumerate(configs):
        audit_blocks = rng.uniform(0.0, 1.0, size=(cfg["n_audit"], k))
        selected = audit_threshold_family(
            audit_blocks,
            thresholds=thresholds,
            violation_threshold=violation_threshold,
            alpha=alpha,
            gamma=cfg["gamma"],
            delta=cfg["delta"],
        )
        if selected.selected_tau is None:
            evaluated = evaluate_abstain_all(test_blocks)
            tau = np.nan
        else:
            evaluated = evaluate_threshold_rule(test_blocks, selected.selected_tau, violation_threshold)
            tau = selected.selected_tau
        summary = evaluated["summary"]
        rows.append(
            {
                "config_id": cfg_id,
                "sweep": cfg["sweep"],
                "n_audit": cfg["n_audit"],
                "gamma": cfg["gamma"],
                "delta": cfg["delta"],
                "tau": tau,
                "selected_false_certification": summary.selective_risk,
                "claim_yield": summary.claim_yield,
                "mean_reward": summary.mean_reward,
                "audit_epsilon": selected.epsilon,
                "feasible_count": sum(1 for rule in selected.rules if rule.feasible),
            }
        )

    df = pd.DataFrame(rows)
    out = OUTPUT_DIR / "toy_selection_failure_sensitivity.csv"
    df.to_csv(out, index=False)
    plot_sensitivity(df)
    return df


def plot_hardened(df: pd.DataFrame) -> None:
    methods = [
        "global_cp_marginal",
        "selected_block_accept_or_abstain",
        "reward_bin_ucb_20",
        "rank_bin_ucb",
        "crc_style_threshold_auditor",
        "accs_v0_finite_rule_auditor",
        "oracle_tau_0_96",
    ]
    labels = {
        "global_cp_marginal": "Global CP",
        "selected_block_accept_or_abstain": "Selected-block",
        "reward_bin_ucb_20": "Reward-bin",
        "rank_bin_ucb": "Rank-bin",
        "crc_style_threshold_auditor": "CRC-style",
        "accs_v0_finite_rule_auditor": "ACCS-v0",
        "oracle_tau_0_96": "Oracle",
    }
    colors = {
        "global_cp_marginal": "#D55E00",
        "selected_block_accept_or_abstain": "#999999",
        "reward_bin_ucb_20": "#E69F00",
        "rank_bin_ucb": "#56B4E9",
        "crc_style_threshold_auditor": "#0072B2",
        "accs_v0_finite_rule_auditor": "#009E73",
        "oracle_tau_0_96": "#CC79A7",
    }
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6))
    for method in methods:
        sub = df[df["method"] == method].sort_values("k")
        axes[0].plot(
            sub["k"],
            sub["selected_false_certification"],
            marker="o",
            label=labels[method],
            color=colors[method],
        )
    axes[0].axhline(0.05, color="black", linestyle="--", linewidth=1.0)
    axes[0].set_xscale("log", base=2)
    axes[0].set_xticks([1, 2, 4, 8, 16, 32])
    axes[0].set_xticklabels(["1", "2", "4", "8", "16", "32"])
    axes[0].set_ylim(-0.02, 0.82)
    axes[0].set_xlabel("Candidate actions per query (K)")
    axes[0].set_ylabel("False certification among issued claims")
    axes[0].set_title("Hardened baselines")
    axes[0].legend(fontsize=7, ncol=2)

    k16 = df[df["k"] == 16]
    plot_methods = [
        "global_cp_marginal",
        "reward_bin_ucb_20",
        "rank_bin_ucb",
        "crc_style_threshold_auditor",
        "accs_v0_finite_rule_auditor",
    ]
    x = np.arange(len(plot_methods))
    width = 0.25
    risk = [float(k16[k16["method"] == m]["selected_false_certification"].iloc[0]) for m in plot_methods]
    claim_yield = [float(k16[k16["method"] == m]["claim_yield"].iloc[0]) for m in plot_methods]
    reward = [float(k16[k16["method"] == m]["mean_reward"].iloc[0]) for m in plot_methods]
    axes[1].bar(x - width, risk, width=width, label="risk", color="#D55E00")
    axes[1].bar(x, claim_yield, width=width, label="yield", color="#0072B2")
    axes[1].bar(x + width, reward, width=width, label="reward", color="#009E73")
    axes[1].axhline(0.05, color="black", linestyle="--", linewidth=1.0)
    axes[1].set_ylim(0.0, 1.05)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(["Global", "Reward", "Rank", "CRC", "ACCS"], rotation=0)
    axes[1].set_title("K=16 risk-yield-reward")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "figure1_selection_amplification_hardened.pdf", bbox_inches="tight")
    fig.savefig(FIGURE_DIR / "figure1_selection_amplification_hardened.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_sensitivity(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13.4, 3.9))
    specs = [
        ("n_audit", "n_audit", "Audit blocks"),
        ("gamma", "gamma", "Minimum yield gamma"),
        ("delta", "delta", "Failure probability delta"),
    ]
    for ax, (sweep, x_col, title) in zip(axes, specs):
        sub = df[df["sweep"] == sweep].sort_values(x_col)
        ax.plot(sub[x_col], sub["selected_false_certification"], marker="o", label="risk", color="#D55E00")
        ax.plot(sub[x_col], sub["claim_yield"], marker="o", label="yield", color="#0072B2")
        ax.plot(sub[x_col], sub["mean_reward"], marker="o", label="reward", color="#009E73")
        ax.axhline(0.05, color="black", linestyle="--", linewidth=1.0)
        if x_col == "n_audit":
            ax.set_xscale("log")
        ax.set_title(title)
        ax.set_ylim(-0.02, 1.05)
        ax.set_xlabel(x_col)
    axes[0].set_ylabel("Metric value")
    axes[-1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "figure1_sensitivity_hardened.pdf", bbox_inches="tight")
    fig.savefig(FIGURE_DIR / "figure1_sensitivity_hardened.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    hardened, sensitivity = run_hardened_experiment()
    k16 = hardened[
        (hardened["k"] == 16)
        & hardened["method"].isin(
            [
                "global_cp_marginal",
                "reward_bin_ucb_20",
                "rank_bin_ucb",
                "crc_style_threshold_auditor",
                "accs_v0_finite_rule_auditor",
            ]
        )
    ]
    print(
        k16[
            [
                "method",
                "selected_false_certification",
                "claim_yield",
                "mean_reward",
                "tau",
            ]
        ].to_string(index=False)
    )
    print("Sensitivity rows:", len(sensitivity))
