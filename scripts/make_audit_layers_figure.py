"""Create the paper figure that links action, proxy-episode, and online audits."""

from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
AAAI_OUT = ROOT / "aaai2027" / "figures"


plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["font.size"] = 7
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False
plt.rcParams["legend.frameon"] = False


COLORS = {
    "cpq": "#0F4D92",
    "coptidice": "#B64342",
    "target": "#767676",
    "neutral": "#D8D8D8",
    "global": "#A8A8A8",
    "crc": "#42949E",
    "accs": "#0F4D92",
    "top": "#B64342",
}


def pct(x: float) -> float:
    return 100.0 * float(x)


def parse_mean(value: str) -> float:
    return float(str(value).split("+/-")[0])


def add_panel_label(ax, label: str) -> None:
    ax.text(
        -0.12,
        1.06,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )


def panel_action_risk_yield(ax) -> None:
    main = pd.read_csv(ROOT / "analysis/paper_assets/table_main_direct_osrl.csv")
    main = main[main["role"].isin(["main_high_signal", "main_stress"])]

    methods = [
        ("Top-selected", "top", "o"),
        ("Global CP", "global", "s"),
        ("CRC-style", "crc", "^"),
        ("ACCS-v0", "accs", "D"),
    ]
    for _, row in main.iterrows():
        proposer = row["proposer"]
        line_color = COLORS["cpq" if proposer == "CPQ" else "coptidice"]
        xs = [
            100.0,
            pct(row["global_cp_yield_mean"]),
            pct(row["crc_yield_mean"]),
            pct(row["accs_yield_mean"]),
        ]
        ys = [
            pct(row["top_selected_false_mean"]),
            pct(row["global_cp_risk_mean"]),
            pct(row["crc_risk_mean"]),
            pct(row["accs_risk_mean"]),
        ]
        ax.plot(xs, ys, color=line_color, alpha=0.30, lw=1.2)
        for (label, color_key, marker), x, y in zip(methods, xs, ys):
            face = COLORS[color_key] if color_key != "accs" else line_color
            ax.scatter(
                x,
                y,
                s=36,
                marker=marker,
                color=face,
                edgecolor="black",
                linewidth=0.5,
                zorder=4,
            )
        dx, dy = {"CPQ": (2.2, 0.13), "COptiDICE": (2.2, -0.13)}[proposer]
        ax.text(xs[-1] + dx, ys[-1] + dy, proposer, color=line_color, fontsize=7, va="center")

    ax.axhline(5, color=COLORS["target"], lw=0.9, ls="--")
    ax.text(4, 5.25, "5% target", color=COLORS["target"], fontsize=6)
    ax.set_xlim(-1, 104)
    ax.set_ylim(-0.4, 9.2)
    ax.set_xlabel("Issued-claim yield (%)")
    ax.set_ylabel("Selected false certification (%)")
    ax.set_title("Action-level query-block audit", loc="left", fontsize=8, pad=4)

    handles = [
        plt.Line2D([0], [0], marker=m, color="none", markerfacecolor=COLORS[c], markeredgecolor="black", markersize=5, label=l)
        for l, c, m in methods[:3]
    ]
    handles.append(
        plt.Line2D([0], [0], marker="D", color="none", markerfacecolor=COLORS["accs"], markeredgecolor="black", markersize=5, label="ACCS-v0")
    )
    ax.legend(handles=handles, loc="upper left", fontsize=6, ncol=2, handletextpad=0.3, columnspacing=0.7)


def panel_episode_proxy(ax) -> None:
    data = pd.read_csv(ROOT / "analysis/paper_assets/table_dsrl_episode_capsweep_proxy_car_q92.csv")
    keep = [
        "accs_v0_support_safety_episode_cap1",
        "accs_v0_support_safety_episode_cap2",
        "accs_v0_support_safety_episode_cap4",
        "accs_v0_support_safety_episode_cap8",
        "accs_v0_support_safety",
    ]
    data = data[data["method"].isin(keep)]
    label_map = {
        "accs_v0_support_safety_episode_cap1": "1",
        "accs_v0_support_safety_episode_cap2": "2",
        "accs_v0_support_safety_episode_cap4": "4",
        "accs_v0_support_safety_episode_cap8": "8",
        "accs_v0_support_safety": "uncapped",
    }
    xpos = {"1": 1, "2": 2, "4": 4, "8": 8, "uncapped": 33}
    for algo, label in [("cpq", "CPQ"), ("coptidice", "COptiDICE")]:
        sub = data[data["algo"] == algo].copy()
        grouped = sub.groupby("method").agg(
            episode_mean=("episode_risk", "mean"),
            episode_std=("episode_risk", "std"),
            block_yield_mean=("block_yield", "mean"),
        )
        xs, ys, es = [], [], []
        for method in keep:
            if method not in grouped.index:
                continue
            cap = label_map[method]
            xs.append(xpos[cap])
            ys.append(pct(grouped.loc[method, "episode_mean"]))
            es.append(pct(grouped.loc[method, "episode_std"]))
        ax.errorbar(
            xs,
            ys,
            yerr=es,
            marker="o",
            lw=1.4,
            capsize=2,
            color=COLORS[algo],
            label=label,
        )
    ax.axhline(5, color=COLORS["target"], lw=0.9, ls="--")
    ax.set_xscale("log", base=2)
    ax.set_xticks([1, 2, 4, 8, 32])
    ax.set_xticklabels(["1", "2", "4", "8", "full"])
    ax.set_xlim(0.8, 40)
    ax.set_ylim(-2, 55)
    ax.set_xlabel("Issued blocks per logged episode")
    ax.set_ylabel("Episode-proxy false rate (%)")
    ax.set_title("Emission budget controls episode accumulation", loc="left", fontsize=8, pad=4)
    ax.legend(loc="upper left", fontsize=6)


def panel_closed_loop(ax) -> None:
    env_files = {
        "Car": ROOT / "analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_car_100x100_diagnostic.csv",
        "Ball": ROOT / "analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_ball_matched_100x100_diagnostic.csv",
        "Drone": ROOT / "analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_drone_matched_100x100_diagnostic.csv",
    }
    rows = []
    for env, path in env_files.items():
        frame = pd.read_csv(path)
        frame = frame[frame["cap"] == 1].copy()
        frame["env_short"] = env
        rows.append(frame)
    data = pd.concat(rows, ignore_index=True)

    envs = ["Car", "Ball", "Drone"]
    x = np.arange(len(envs))
    width = 0.34
    for offset, algo, label in [(-width / 2, "cpq", "CPQ"), (width / 2, "coptidice", "COptiDICE")]:
        vals = []
        for env in envs:
            row = data[(data["env_short"] == env) & (data["algo"] == algo)].iloc[0]
            vals.append(pct(row["test_ep_cp95_upper"]))
        ax.bar(
            x + offset,
            vals,
            width=width,
            color=COLORS[algo],
            edgecolor="black",
            linewidth=0.5,
            label=label,
        )

    ax.axhline(5, color=COLORS["target"], lw=0.9, ls="--")
    ax.text(
        -0.45,
        9.0,
        "5% target",
        color=COLORS["target"],
        fontsize=6,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.2},
    )
    ax.set_xticks(x)
    ax.set_xticklabels(envs)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Closed-loop episode U95 (%)")
    ax.set_title("Fixed first-cap online audit", loc="left", fontsize=8, pad=4)
    ax.legend(loc="upper left", fontsize=6)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    AAAI_OUT.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(7.1, 4.1))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.05, 1.0], height_ratios=[1.0, 1.0], hspace=0.55, wspace=0.35)
    ax_a = fig.add_subplot(gs[:, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 1])

    panel_action_risk_yield(ax_a)
    panel_episode_proxy(ax_b)
    panel_closed_loop(ax_c)

    add_panel_label(ax_a, "a")
    add_panel_label(ax_b, "b")
    add_panel_label(ax_c, "c")

    base = OUT / "figure2_audit_layers"
    for ext in ["pdf", "svg", "png"]:
        fig.savefig(base.with_suffix(f".{ext}"), bbox_inches="tight", dpi=600)
        shutil.copy2(base.with_suffix(f".{ext}"), AAAI_OUT / base.with_suffix(f".{ext}").name)
    plt.close(fig)


if __name__ == "__main__":
    main()
