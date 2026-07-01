"""Exact selection-amplification toy for AAAI_2.

This script creates the first local evidence package:

    proposal-level false rate = 4%
    selected-action false certification = 1 - 0.96^K

It also runs ACCS-v0, a finite-rule threshold auditor selected on independent
audit blocks.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eval_metrics import closed_form_selection_risk
from selective_auditor import (
    audit_threshold_family,
    evaluate_abstain_all,
    evaluate_accept_all,
    evaluate_threshold_rule,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
FIGURE_DIR = ROOT / "figures"


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


def run_experiment(
    seed: int = 20260623,
    n_test: int = 200_000,
    n_audit: int = 50_000,
    alpha: float = 0.05,
    gamma: float = 0.70,
    delta: float = 0.05,
    violation_threshold: float = 0.96,
):
    rng = np.random.default_rng(seed)
    ks = [1, 2, 4, 8, 16, 32]
    thresholds = np.unique(
        np.concatenate(
            [
                np.linspace(0.70, 1.0, 301),
                np.array([violation_threshold]),
            ]
        )
    )
    rows = []
    selected_rules = {}

    for k in ks:
        x_test = rng.uniform(0.0, 1.0, size=(n_test, k))
        x_audit = rng.uniform(0.0, 1.0, size=(n_audit, k))
        exact_risk = closed_form_selection_risk(1.0 - violation_threshold, k)

        accept_all = evaluate_accept_all(x_test, violation_threshold=violation_threshold)
        add_row(
            rows,
            k,
            "uncalibrated_score_accept_all",
            accept_all,
            proposal_false_rate=1.0 - violation_threshold,
            extra={"closed_form_selected_risk": exact_risk},
        )

        global_cp = evaluate_accept_all(x_test, violation_threshold=violation_threshold)
        add_row(
            rows,
            k,
            "global_cp_marginal",
            global_cp,
            proposal_false_rate=1.0 - violation_threshold,
            extra={"closed_form_selected_risk": exact_risk},
        )

        irrelevant_group_cp = evaluate_accept_all(x_test, violation_threshold=violation_threshold)
        add_row(
            rows,
            k,
            "group_cp_irrelevant_groups",
            irrelevant_group_cp,
            proposal_false_rate=1.0 - violation_threshold,
            extra={"closed_form_selected_risk": exact_risk},
        )

        if 1.0 - violation_threshold <= alpha / k:
            bonferroni = evaluate_accept_all(x_test, violation_threshold=violation_threshold)
            bonferroni_note = "accept_all"
        else:
            bonferroni = evaluate_abstain_all(x_test)
            bonferroni_note = "abstain_all_binary_residual"
        add_row(
            rows,
            k,
            "bonferroni_alpha_over_k",
            bonferroni,
            proposal_false_rate=1.0 - violation_threshold,
            extra={"closed_form_selected_risk": exact_risk, "note": bonferroni_note},
        )

        oracle = evaluate_threshold_rule(
            x_test,
            tau=violation_threshold,
            violation_threshold=violation_threshold,
        )
        add_row(
            rows,
            k,
            "oracle_tau_0_96",
            oracle,
            proposal_false_rate=0.0,
            extra={"tau": violation_threshold, "closed_form_selected_risk": 0.0},
        )

        selected = audit_threshold_family(
            audit_blocks=x_audit,
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
            accs_extra = {
                "tau": np.nan,
                "audit_risk_ucb": np.nan,
                "audit_yield_lcb": np.nan,
                "audit_epsilon": selected.epsilon,
            }
        else:
            accs = evaluate_threshold_rule(
                x_test,
                tau=selected.selected_tau,
                violation_threshold=violation_threshold,
            )
            accs_extra = {
                "tau": selected.selected_tau,
                "audit_risk_ucb": selected.selected.risk_ucb,
                "audit_yield_lcb": selected.selected.yield_lcb,
                "audit_epsilon": selected.epsilon,
            }
        add_row(
            rows,
            k,
            "accs_v0_finite_rule_auditor",
            accs,
            proposal_false_rate=np.nan,
            extra=accs_extra,
        )

    df = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / "toy_selection_failure.csv"
    json_path = OUTPUT_DIR / "toy_selection_failure_summary.json"
    df.to_csv(csv_path, index=False)

    summary = {
        "seed": seed,
        "n_test": n_test,
        "n_audit": n_audit,
        "alpha": alpha,
        "gamma": gamma,
        "delta": delta,
        "violation_threshold": violation_threshold,
        "per_action_false_rate": 1.0 - violation_threshold,
        "selected_rules": selected_rules,
        "outputs": {
            "csv": str(csv_path.relative_to(ROOT)),
            "figure_pdf": "figures/figure1_selection_amplification.pdf",
            "figure_png": "figures/figure1_selection_amplification.png",
        },
    }
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    plot_figure(df)
    return df, summary


def plot_figure(df: pd.DataFrame) -> None:
    methods = [
        "global_cp_marginal",
        "bonferroni_alpha_over_k",
        "accs_v0_finite_rule_auditor",
        "oracle_tau_0_96",
    ]
    labels = {
        "global_cp_marginal": "Global CP / accept all",
        "bonferroni_alpha_over_k": "Bonferroni alpha/K",
        "accs_v0_finite_rule_auditor": "ACCS-v0",
        "oracle_tau_0_96": "Oracle tau=0.96",
    }
    colors = {
        "global_cp_marginal": "#D55E00",
        "bonferroni_alpha_over_k": "#0072B2",
        "accs_v0_finite_rule_auditor": "#009E73",
        "oracle_tau_0_96": "#CC79A7",
    }
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))

    for method in methods:
        sub = df[df["method"] == method].sort_values("k")
        axes[0].plot(
            sub["k"],
            sub["selected_false_certification"],
            marker="o",
            label=labels[method],
            color=colors[method],
        )
    axes[0].axhline(0.05, color="black", linestyle="--", linewidth=1.0, label="target 5%")
    axes[0].set_xscale("log", base=2)
    axes[0].set_xticks([1, 2, 4, 8, 16, 32])
    axes[0].set_xticklabels(["1", "2", "4", "8", "16", "32"])
    axes[0].set_ylim(-0.02, 0.82)
    axes[0].set_xlabel("Candidate actions per query (K)")
    axes[0].set_ylabel("False certification among issued claims")
    axes[0].set_title("Selection amplifies marginal failures")
    axes[0].legend(fontsize=8)

    k16 = df[df["k"] == 16].copy()
    plot_methods = [
        "global_cp_marginal",
        "bonferroni_alpha_over_k",
        "accs_v0_finite_rule_auditor",
        "oracle_tau_0_96",
    ]
    x = np.arange(len(plot_methods))
    width = 0.26
    risk = [float(k16[k16["method"] == m]["selected_false_certification"].iloc[0]) for m in plot_methods]
    claim_yield = [float(k16[k16["method"] == m]["claim_yield"].iloc[0]) for m in plot_methods]
    reward = [float(k16[k16["method"] == m]["mean_reward"].iloc[0]) for m in plot_methods]
    axes[1].bar(x - width, risk, width=width, label="risk", color="#D55E00")
    axes[1].bar(x, claim_yield, width=width, label="yield", color="#0072B2")
    axes[1].bar(x + width, reward, width=width, label="reward", color="#009E73")
    axes[1].axhline(0.05, color="black", linestyle="--", linewidth=1.0)
    axes[1].set_ylim(0.0, 1.05)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(["Global", "Bonf.", "ACCS", "Oracle"], rotation=0)
    axes[1].set_title("K=16 risk-yield-reward tradeoff")
    axes[1].legend(fontsize=8)

    fig.tight_layout()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_DIR / "figure1_selection_amplification.pdf", bbox_inches="tight")
    fig.savefig(FIGURE_DIR / "figure1_selection_amplification.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    frame, info = run_experiment()
    k16 = frame[(frame["k"] == 16) & (frame["method"].isin(["global_cp_marginal", "accs_v0_finite_rule_auditor"]))]
    print(k16[["k", "method", "selected_false_certification", "claim_yield", "mean_reward", "tau"]].to_string(index=False))
    print(json.dumps(info["outputs"], indent=2))
