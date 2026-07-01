"""Summarize CAPSIQL checkpoint pilot JSON outputs into CSV and Markdown."""

from __future__ import annotations

import argparse
import csv
import glob
import json
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]


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
        if payload.get("proposer") != "official_dsrl_capsiql_checkpoint_proposer_v1":
            continue
        auditors = {row["name"]: row for row in payload["auditors"]}
        cfg = payload["config"]
        diag = payload["diagnostics"]
        none = auditors["none_original_proposer"]
        crc = auditors["crc_style_safety_threshold"]
        accs = auditors["accs_v0_support_safety"]
        reward_bin = auditors["reward_bin_ucb_20"]
        rows.append(
            {
                "file": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
                "env": payload["env"],
                "seed": int(cfg["seed"]),
                "risk_quantile": float(cfg["risk_quantile"]),
                "reward_risk_bonus": float(cfg["reward_risk_bonus"]),
                "model_reward_weight": float(cfg["model_reward_weight"]),
                "model_cost_weight": float(cfg["model_cost_weight"]),
                "candidate_false": float(diag["test_candidate_false_rate"]),
                "top_false": float(diag["test_top_reward_false_rate"]),
                "selection_gap": float(diag["test_top_reward_false_rate"])
                - float(diag["test_candidate_false_rate"]),
                "none_reward": float(none["normalized_reward"]),
                "reward_bin_risk": float(reward_bin["selected_false_certification"]),
                "reward_bin_yield": float(reward_bin["claim_yield"]),
                "crc_risk": float(crc["selected_false_certification"]),
                "crc_yield": float(crc["claim_yield"]),
                "crc_reward": float(crc["normalized_reward"]),
                "accs_risk": float(accs["selected_false_certification"]),
                "accs_yield": float(accs["claim_yield"]),
                "accs_reward": float(accs["normalized_reward"]),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            row["seed"],
            row["risk_quantile"],
            row["reward_risk_bonus"],
            row["model_reward_weight"],
            row["model_cost_weight"],
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
        "risk_quantile",
        "reward_risk_bonus",
        "model_reward_weight",
        "model_cost_weight",
        "candidate_false",
        "top_false",
        "selection_gap",
        "none_reward",
        "crc_risk",
        "crc_yield",
        "accs_risk",
        "accs_yield",
        "accs_reward",
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
        "reward_bin_risk",
        "reward_bin_yield",
        "crc_risk",
        "crc_yield",
        "crc_reward",
        "accs_risk",
        "accs_yield",
        "accs_reward",
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
        "# CAPSIQL Checkpoint Pilot Summary\n\n"
        + "\n".join(lines)
        + "\n\n## Aggregate\n\n"
        + "\n".join(aggregate_lines)
        + "\n",
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
        default=ROOT / "analysis" / "paper_assets" / "table_dsrl_capsiql_checkpoint_pilots.csv",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=ROOT / "outputs" / "phase_dsrl_capsiql_checkpoint_summary.md",
    )
    args = parser.parse_args()
    patterns = args.pattern or ["outputs/phase_dsrl_capsiql_checkpoint*_server.json"]
    rows = load_rows(patterns)
    if not rows:
        raise SystemExit("No CAPSIQL checkpoint pilot JSON files found.")
    write_outputs(rows, args.out_csv, args.out_md)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")


if __name__ == "__main__":
    main()
