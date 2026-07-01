"""Local toy for off-policy deployment-query shift.

The audit law P observes selected-query scores x uniformly on [0, 1]. The
deployment law Q_a tilts toward high-reward, high-risk selected queries with
density q_a(x) = a x^(a-1). A threshold that is acceptable under P can therefore
fail after deployment-query shift unless the audit uses explicit density ratios
or a support cap.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
FIGURE_DIR = ROOT / "figures"


@dataclass(frozen=True)
class RuleFit:
    tau: float
    audit_risk: float
    audit_yield: float
    audit_reward: float
    audit_ess: float


def sample_audit(rng: np.random.Generator, n: int) -> np.ndarray:
    return rng.uniform(0.0, 1.0, size=n)


def sample_deployment(rng: np.random.Generator, n: int, shift_alpha: float) -> np.ndarray:
    # If U is uniform, U ** (1 / a) has density a x^(a-1).
    return rng.uniform(0.0, 1.0, size=n) ** (1.0 / shift_alpha)


def density_ratio_q_over_p(x: np.ndarray, shift_alpha: float, weight_cap: float | None) -> np.ndarray:
    weights = shift_alpha * np.clip(x, 0.0, 1.0) ** (shift_alpha - 1.0)
    if weight_cap is not None:
        weights = np.minimum(weights, weight_cap)
    return weights.astype(float)


def evaluate_tau(
    x: np.ndarray,
    tau: float,
    unsafe_threshold: float,
    weights: np.ndarray | None = None,
) -> dict:
    issued = x <= tau
    failure = issued & (x > unsafe_threshold)
    reward = np.where(issued, x, 0.0)
    if weights is None:
        denom = float(x.size)
        issued_mass = float(issued.sum())
        failure_mass = float(failure.sum())
        reward_mass = float(reward.sum())
        ess = issued_mass
    else:
        w = np.asarray(weights, dtype=float)
        denom = float(w.sum())
        issued_weights = w[issued]
        issued_mass = float(issued_weights.sum())
        failure_mass = float(w[failure].sum())
        reward_mass = float((w * reward).sum())
        ess = 0.0
        if issued_weights.size:
            sq = float(np.square(issued_weights).sum())
            ess = 0.0 if sq <= 0.0 else float(issued_mass * issued_mass / sq)

    risk = 0.0 if issued_mass <= 0.0 else failure_mass / issued_mass
    claim_yield = 0.0 if denom <= 0.0 else issued_mass / denom
    mean_reward = 0.0 if denom <= 0.0 else reward_mass / denom
    return {
        "issued_mass": issued_mass,
        "failures": failure_mass,
        "risk": float(risk),
        "claim_yield": float(claim_yield),
        "mean_reward": float(mean_reward),
        "ess": float(ess),
    }


def fit_rule(
    x_audit: np.ndarray,
    thresholds: np.ndarray,
    unsafe_threshold: float,
    alpha: float,
    min_yield: float,
    weights: np.ndarray | None = None,
) -> RuleFit:
    candidates = []
    for tau in thresholds:
        metrics = evaluate_tau(x_audit, tau, unsafe_threshold, weights=weights)
        if metrics["risk"] <= alpha and metrics["claim_yield"] >= min_yield:
            candidates.append((tau, metrics))
    if not candidates:
        tau = float(thresholds[0])
        metrics = evaluate_tau(x_audit, tau, unsafe_threshold, weights=weights)
    else:
        tau, metrics = max(candidates, key=lambda item: (item[1]["mean_reward"], item[0]))
    return RuleFit(
        tau=float(tau),
        audit_risk=metrics["risk"],
        audit_yield=metrics["claim_yield"],
        audit_reward=metrics["mean_reward"],
        audit_ess=metrics["ess"],
    )


def add_row(
    rows: list[dict],
    shift_alpha: float,
    method: str,
    fit: RuleFit,
    x_test_q: np.ndarray,
    unsafe_threshold: float,
) -> None:
    test = evaluate_tau(x_test_q, fit.tau, unsafe_threshold)
    rows.append(
        {
            "shift_alpha": float(shift_alpha),
            "method": method,
            "tau": fit.tau,
            "audit_risk": fit.audit_risk,
            "audit_yield": fit.audit_yield,
            "audit_reward": fit.audit_reward,
            "audit_ess": fit.audit_ess,
            "deployment_risk": test["risk"],
            "deployment_yield": test["claim_yield"],
            "deployment_reward": test["mean_reward"],
            "deployment_issued": test["issued_mass"],
            "deployment_failures": test["failures"],
        }
    )


def run_experiment(
    seed: int = 20260630,
    n_audit: int = 20_000,
    n_test: int = 200_000,
    alpha: float = 0.05,
    min_yield: float = 0.20,
    unsafe_threshold: float = 0.85,
    weight_cap: float = 8.0,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    thresholds = np.round(np.linspace(0.60, 0.96, 73), 4)
    shift_alphas = [1.0, 2.0, 4.0, 8.0]
    rows: list[dict] = []

    x_audit = sample_audit(rng, n_audit)
    for shift_alpha in shift_alphas:
        x_test_q = sample_deployment(rng, n_test, shift_alpha)
        weights = density_ratio_q_over_p(x_audit, shift_alpha, weight_cap=None)
        capped_weights = density_ratio_q_over_p(x_audit, shift_alpha, weight_cap=weight_cap)

        unweighted = fit_rule(
            x_audit,
            thresholds,
            unsafe_threshold,
            alpha=alpha,
            min_yield=min_yield,
            weights=None,
        )
        weighted = fit_rule(
            x_audit,
            thresholds,
            unsafe_threshold,
            alpha=alpha,
            min_yield=min_yield,
            weights=weights,
        )
        capped_weighted = fit_rule(
            x_audit,
            thresholds,
            unsafe_threshold,
            alpha=alpha,
            min_yield=min_yield,
            weights=capped_weights,
        )
        support_cap = RuleFit(
            tau=min(unweighted.tau, unsafe_threshold),
            audit_risk=0.0,
            audit_yield=float((x_audit <= unsafe_threshold).mean()),
            audit_reward=float(np.where(x_audit <= unsafe_threshold, x_audit, 0.0).mean()),
            audit_ess=float((x_audit <= unsafe_threshold).sum()),
        )
        oracle = fit_rule(
            x_test_q,
            thresholds,
            unsafe_threshold,
            alpha=alpha,
            min_yield=min_yield,
            weights=None,
        )

        add_row(rows, shift_alpha, "unweighted_audit_P", unweighted, x_test_q, unsafe_threshold)
        add_row(rows, shift_alpha, "weighted_known_ratio", weighted, x_test_q, unsafe_threshold)
        add_row(rows, shift_alpha, "weighted_ratio_cap8", capped_weighted, x_test_q, unsafe_threshold)
        add_row(rows, shift_alpha, "support_cap_at_boundary", support_cap, x_test_q, unsafe_threshold)
        add_row(rows, shift_alpha, "oracle_audit_Q", oracle, x_test_q, unsafe_threshold)

    df = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUTPUT_DIR / "toy_offpolicy_shift.csv"
    df.to_csv(out_csv, index=False)
    write_summary(df, out_csv)
    plot_figure(df)
    return df


def write_summary(df: pd.DataFrame, out_csv: Path) -> None:
    lines = [
        "# Off-Policy Query-Shift Toy",
        "",
        f"CSV: `{out_csv.as_posix()}`",
        "",
        "Audit law P is uniform over selected-query score x. Deployment law Q tilts",
        "toward high-reward/high-risk x with density a x^(a-1). Unsafe claims are",
        "those issued with x > 0.85. Values below are deployment metrics.",
        "",
        "| Shift a | Method | Tau | Risk | Yield | Reward | Audit ESS |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in df.sort_values(["shift_alpha", "method"]).iterrows():
        lines.append(
            "| {shift:.1f} | {method} | {tau:.3f} | {risk:.4f} | {yield_:.4f} | {reward:.4f} | {ess:.1f} |".format(
                shift=row["shift_alpha"],
                method=row["method"],
                tau=row["tau"],
                risk=row["deployment_risk"],
                yield_=row["deployment_yield"],
                reward=row["deployment_reward"],
                ess=row["audit_ess"],
            )
        )
    lines.extend(
        [
            "",
            "Interpretation: unweighted audit estimates risk under P and can pass a",
            "threshold that violates the target under shifted deployment Q. Known-ratio",
            "weighting tracks the Q target but loses effective sample size under strong",
            "tilt. A hard support cap is conservative but makes the abstention/yield cost",
            "explicit.",
            "",
        ]
    )
    (OUTPUT_DIR / "toy_offpolicy_shift_summary.md").write_text("\n".join(lines), encoding="utf-8")


def plot_figure(df: pd.DataFrame) -> None:
    methods = [
        ("unweighted_audit_P", "Unweighted P audit", "#D55E00"),
        ("weighted_known_ratio", "Known-ratio audit", "#0072B2"),
        ("weighted_ratio_cap8", "Capped-ratio audit", "#CC79A7"),
        ("support_cap_at_boundary", "Support cap", "#009E73"),
        ("oracle_audit_Q", "Oracle Q audit", "#000000"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.1), sharex=True)
    for method, label, color in methods:
        sub = df[df["method"] == method].sort_values("shift_alpha")
        axes[0].plot(sub["shift_alpha"], sub["deployment_risk"], marker="o", label=label, color=color)
        axes[1].plot(sub["shift_alpha"], sub["deployment_yield"], marker="o", label=label, color=color)
    axes[0].axhline(0.05, linestyle="--", linewidth=1.0, color="0.35")
    axes[0].set_ylabel("Deployment false certification")
    axes[1].set_ylabel("Deployment claim yield")
    for ax in axes:
        ax.set_xlabel("Deployment tilt a")
        ax.set_xticks([1.0, 2.0, 4.0, 8.0])
        ax.set_ylim(bottom=0.0)
    axes[0].set_ylim(0.0, max(0.12, float(df["deployment_risk"].max()) * 1.12))
    axes[1].set_ylim(0.0, 1.02)
    axes[1].legend(fontsize=7, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "figure4_offpolicy_shift.pdf", bbox_inches="tight")
    fig.savefig(FIGURE_DIR / "figure4_offpolicy_shift.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    frame = run_experiment()
    focus = frame[frame["shift_alpha"] == 8.0].sort_values("deployment_risk")
    print(focus.to_string(index=False))
