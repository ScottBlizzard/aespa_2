"""Local toy showing residual costs are continuation-policy-specific."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eval_metrics import closed_form_selection_risk
from selective_auditor import evaluate_accept_all, evaluate_threshold_rule


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
FIGURE_DIR = ROOT / "figures"


def run_experiment(
    seed: int = 20260624,
    n_test: int = 200_000,
    unsafe_threshold: float = 0.90,
):
    rng = np.random.default_rng(seed)
    ks = [1, 2, 4, 8, 16, 32]
    rows = []

    for k in ks:
        x = rng.uniform(0.0, 1.0, size=(n_test, k))

        behavior = evaluate_accept_all(x, violation_threshold=1.01)
        deployment = evaluate_accept_all(x, violation_threshold=unsafe_threshold)
        support_aware = evaluate_threshold_rule(
            x,
            tau=unsafe_threshold,
            violation_threshold=unsafe_threshold,
        )

        rows.append(
            {
                "k": k,
                "method": "behavior_rescue_labels",
                "description": "offline behavior continuation always rescues",
                "selected_false_certification": behavior["summary"].selective_risk,
                "claim_yield": behavior["summary"].claim_yield,
                "mean_reward": behavior["summary"].mean_reward,
                "closed_form_deployment_risk": 0.0,
            }
        )
        rows.append(
            {
                "k": k,
                "method": "deployment_exploit_accept_all",
                "description": "same first actions, deployment continuation exploits",
                "selected_false_certification": deployment["summary"].selective_risk,
                "claim_yield": deployment["summary"].claim_yield,
                "mean_reward": deployment["summary"].mean_reward,
                "closed_form_deployment_risk": closed_form_selection_risk(1.0 - unsafe_threshold, k),
            }
        )
        rows.append(
            {
                "k": k,
                "method": "declared_policy_support_aware_tau",
                "description": "auditor uses deployment residual target and caps unsafe x",
                "selected_false_certification": support_aware["summary"].selective_risk,
                "claim_yield": support_aware["summary"].claim_yield,
                "mean_reward": support_aware["summary"].mean_reward,
                "closed_form_deployment_risk": 0.0,
            }
        )

    df = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / "toy_policy_mismatch.csv"
    df.to_csv(out, index=False)
    plot_figure(df)
    return df


def plot_figure(df: pd.DataFrame) -> None:
    labels = {
        "behavior_rescue_labels": "Behavior labels",
        "deployment_exploit_accept_all": "Deployment accept-all",
        "declared_policy_support_aware_tau": "Policy-aware cap",
    }
    colors = {
        "behavior_rescue_labels": "#0072B2",
        "deployment_exploit_accept_all": "#D55E00",
        "declared_policy_support_aware_tau": "#009E73",
    }
    fig, ax = plt.subplots(figsize=(6.4, 4.1))
    for method, label in labels.items():
        sub = df[df["method"] == method].sort_values("k")
        ax.plot(
            sub["k"],
            sub["selected_false_certification"],
            marker="o",
            label=label,
            color=colors[method],
        )
    ax.set_xscale("log", base=2)
    ax.set_xticks([1, 2, 4, 8, 16, 32])
    ax.set_xticklabels(["1", "2", "4", "8", "16", "32"])
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("Candidate actions per query (K)")
    ax.set_ylabel("False certification among issued claims")
    ax.set_title("Residual certificates depend on continuation policy")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "figure2_policy_mismatch.pdf", bbox_inches="tight")
    fig.savefig(FIGURE_DIR / "figure2_policy_mismatch.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    frame = run_experiment()
    print(frame[frame["k"] == 16].to_string(index=False))
