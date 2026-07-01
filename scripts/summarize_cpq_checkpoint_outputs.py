"""Summarize CPQ checkpoint pilot JSON outputs into CSV and Markdown."""

from __future__ import annotations

import argparse
import csv
import glob
import json
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]


def checkpoint_tag(checkpoint: str) -> str:
    path = Path(checkpoint)
    if path.name == "model_best.pt":
        return "model_best"
    if path.name == "model.pt":
        return "model"
    return path.stem or checkpoint


def load_rows(patterns: Iterable[str]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    paths: List[Path] = []
    for pattern in patterns:
        paths.extend(sorted(ROOT.glob(pattern)))
        paths.extend(Path(p) for p in sorted(glob.glob(pattern)) if Path(p).is_absolute())
    seen = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen or not path.exists():
            continue
        seen.add(resolved)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("proposer") != "official_dsrl_cpq_checkpoint_proposer_v1":
            continue
        auditors = {row["name"]: row for row in payload["auditors"]}
        cfg = payload["config"]
        diag = payload["diagnostics"]
        test_diag = diag.get("test", {})
        none = auditors["none_original_proposer"]
        global_cp = auditors["global_candidate_cp"]
        crc = auditors["crc_style_safety_threshold"]
        accs = auditors["accs_v0_support_safety"]
        reward_bin = auditors["reward_bin_ucb_20"]
        rows.append(
            {
                "file": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
                "env": payload["env"],
                "seed": int(cfg["seed"]),
                "checkpoint_tag": checkpoint_tag(payload["checkpoint"]),
                "risk_quantile": float(cfg["risk_quantile"]),
                "proposal_samples": int(cfg["proposal_samples"]),
                "candidate_false": float(diag["test_candidate_false_rate"]),
                "top_false": float(diag["test_top_reward_false_rate"]),
                "selection_gap": float(diag["test_top_reward_false_rate"])
                - float(diag["test_candidate_false_rate"]),
                "none_reward": float(none["normalized_reward"]),
                "global_risk": float(global_cp["selected_false_certification"]),
                "global_yield": float(global_cp["claim_yield"]),
                "reward_bin_risk": float(reward_bin["selected_false_certification"]),
                "reward_bin_yield": float(reward_bin["claim_yield"]),
                "crc_risk": float(crc["selected_false_certification"]),
                "crc_yield": float(crc["claim_yield"]),
                "crc_reward": float(crc["normalized_reward"]),
                "accs_risk": float(accs["selected_false_certification"]),
                "accs_yield": float(accs["claim_yield"]),
                "accs_reward": float(accs["normalized_reward"]),
                "action_match_mean": float(test_diag["action_match_distance_mean"]),
                "action_match_median": float(test_diag["action_match_distance_median"]),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            row["seed"],
            row["risk_quantile"],
            row["checkpoint_tag"],
            row["file"],
        ),
    )


def write_outputs(rows: List[Dict[str, object]], out_csv: Path, out_md: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    cols = [
        "seed",
        "checkpoint_tag",
        "risk_quantile",
        "candidate_false",
        "top_false",
        "selection_gap",
        "none_reward",
        "global_risk",
        "global_yield",
        "crc_risk",
        "crc_yield",
        "accs_risk",
        "accs_yield",
        "accs_reward",
        "action_match_mean",
        "action_match_median",
    ]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in rows:
        values = []
        for col in cols:
            value = row[col]
            values.append(f"{value:.6f}" if isinstance(value, float) else str(value))
        lines.append("| " + " | ".join(values) + " |")

    metric_cols = [
        "candidate_false",
        "top_false",
        "selection_gap",
        "none_reward",
        "global_risk",
        "global_yield",
        "reward_bin_risk",
        "reward_bin_yield",
        "crc_risk",
        "crc_yield",
        "crc_reward",
        "accs_risk",
        "accs_yield",
        "accs_reward",
        "action_match_mean",
        "action_match_median",
    ]
    aggregate_lines = [
        "| metric | mean | std |",
        "| --- | ---: | ---: |",
    ]
    for col in metric_cols:
        values = [float(row[col]) for row in rows]
        mean = sum(values) / len(values)
        var = sum((value - mean) ** 2 for value in values) / len(values)
        aggregate_lines.append(f"| {col} | {mean:.6f} | {var ** 0.5:.6f} |")

    out_md.write_text(
        "# CPQ Checkpoint Pilot Summary\n\n"
        + "\n".join(lines)
        + "\n\n## Aggregate\n\n"
        + "\n".join(aggregate_lines)
        + "\n\n"
        + "Notes: `top_false` is the unaudited top-reward proposer violation rate; "
        + "`accs_*` and `crc_*` are audited risk/yield/reward metrics on the same test blocks.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pattern",
        action="append",
        default=None,
        help="Glob pattern relative to the project root. Can be repeated.",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "analysis" / "paper_assets" / "table_dsrl_cpq_checkpoint_pilots.csv",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=ROOT / "outputs" / "phase_dsrl_cpq_checkpoint_summary.md",
    )
    args = parser.parse_args()
    patterns = args.pattern or ["outputs/phase_dsrl_cpq_checkpoint*_server.json"]
    rows = load_rows(patterns)
    if not rows:
        raise SystemExit("No CPQ checkpoint pilot JSON files found.")
    write_outputs(rows, args.out_csv, args.out_md)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")


if __name__ == "__main__":
    main()
