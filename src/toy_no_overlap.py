"""Local toy showing unsupported actions cannot be certified from offline data."""

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
    seed: int = 20260625,
    n_test: int = 200_000,
    support_max: float = 0.90,
):
    rng = np.random.default_rng(seed)
    ks = [1, 2, 4, 8, 16, 32]
    rows = []

    for k in ks:
        x = rng.uniform(0.0, 1.0, size=(n_test, k))

        world0_naive = evaluate_accept_all(x, violation_threshold=1.01)
        world1_naive = evaluate_accept_all(x, violation_threshold=support_max)
        support_aware_world1 = evaluate_threshold_rule(
            x,
            tau=support_max,
            violation_threshold=support_max,
        )

        rows.append(
            {
                "k": k,
                "world": "M0_safe_unsupported",
                "method": "naive_certify_unsupported",
                "selected_false_certification": world0_naive["summary"].selective_risk,
                "claim_yield": world0_naive["summary"].claim_yield,
                "mean_reward": world0_naive["summary"].mean_reward,
                "unsupported_selected_rate": closed_form_selection_risk(1.0 - support_max, k),
            }
        )
        rows.append(
            {
                "k": k,
                "world": "M1_unsafe_unsupported",
                "method": "naive_certify_unsupported",
                "selected_false_certification": world1_naive["summary"].selective_risk,
                "claim_yield": world1_naive["summary"].claim_yield,
                "mean_reward": world1_naive["summary"].mean_reward,
                "unsupported_selected_rate": closed_form_selection_risk(1.0 - support_max, k),
            }
        )
        rows.append(
            {
                "k": k,
                "world": "M1_unsafe_unsupported",
                "method": "support_aware_abstain_above_support",
                "selected_false_certification": support_aware_world1["summary"].selective_risk,
                "claim_yield": support_aware_world1["summary"].claim_yield,
                "mean_reward": support_aware_world1["summary"].mean_reward,
                "unsupported_selected_rate": 0.0,
            }
        )

    df = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / "toy_no_overlap.csv"
    df.to_csv(out, index=False)
    plot_figure(df)
    return df


def plot_figure(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.1))
    plot_specs = [
        ("M0_safe_unsupported", "naive_certify_unsupported", "Naive in M0", "#0072B2"),
        ("M1_unsafe_unsupported", "naive_certify_unsupported", "Naive in M1", "#D55E00"),
        (
            "M1_unsafe_unsupported",
            "support_aware_abstain_above_support",
            "Support-aware in M1",
            "#009E73",
        ),
    ]
    for world, method, label, color in plot_specs:
        sub = df[(df["world"] == world) & (df["method"] == method)].sort_values("k")
        axes[0].plot(
            sub["k"],
            sub["selected_false_certification"],
            marker="o",
            label=label,
            color=color,
        )
        axes[1].plot(
            sub["k"],
            sub["claim_yield"],
            marker="o",
            label=label,
            color=color,
        )

    for ax in axes:
        ax.set_xscale("log", base=2)
        ax.set_xticks([1, 2, 4, 8, 16, 32])
        ax.set_xticklabels(["1", "2", "4", "8", "16", "32"])
        ax.set_xlabel("Candidate actions per query (K)")
    axes[0].set_ylim(-0.02, 1.02)
    axes[0].set_ylabel("False certification")
    axes[0].set_title("Same offline data, opposite unsupported worlds")
    axes[1].set_ylim(-0.02, 1.05)
    axes[1].set_ylabel("Claim yield")
    axes[1].set_title("Abstention preserves evidence validity")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "figure3_no_overlap.pdf", bbox_inches="tight")
    fig.savefig(FIGURE_DIR / "figure3_no_overlap.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    frame = run_experiment()
    print(frame[frame["k"] == 16].to_string(index=False))
