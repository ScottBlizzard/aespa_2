"""Summarize direct-OSRL horizon stress JSON outputs.

The script reads CPQ/COptiDICE/CAPSIQL checkpoint evaluator JSON files and
aggregates selected-claim risk/yield by proposer and residual-label horizon.
It is intended for stress tests such as H=20 versus H=80 under the same
fixed query-bank/auditor contract.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]


PROPOSER_NAMES = {
    "official_dsrl_capsiql_checkpoint_proposer_v1": "CAPSIQL",
    "official_dsrl_cpq_checkpoint_proposer_v1": "CPQ",
    "official_dsrl_coptidice_checkpoint_proposer_v1": "COptiDICE",
}


def checkpoint_tag(checkpoint: str) -> str:
    path = Path(checkpoint)
    if path.name in {"model_best.pt", "model.pt"}:
        return path.name.removesuffix(".pt")
    return path.stem or checkpoint


def load_paths(patterns: Iterable[str]) -> List[Path]:
    paths: List[Path] = []
    for pattern in patterns:
        paths.extend(sorted(ROOT.glob(pattern)))
        paths.extend(Path(p) for p in sorted(glob.glob(pattern)) if Path(p).is_absolute())
    seen = set()
    unique: List[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen or not path.exists():
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def method(payload: Dict[str, object], name: str) -> Dict[str, object]:
    auditors = {row["name"]: row for row in payload["auditors"]}
    return auditors[name]


def load_rows(patterns: Iterable[str]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for path in load_paths(patterns):
        payload = json.loads(path.read_text(encoding="utf-8"))
        proposer = payload.get("proposer")
        if proposer not in PROPOSER_NAMES:
            continue
        cfg = payload["config"]
        diag = payload["diagnostics"]
        test_diag = diag.get("test", {})
        none = method(payload, "none_original_proposer")
        global_cp = method(payload, "global_candidate_cp")
        reward_bin = method(payload, "reward_bin_ucb_20")
        crc = method(payload, "crc_style_safety_threshold")
        accs = method(payload, "accs_v0_support_safety")
        rows.append(
            {
                "file": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
                "proposer": PROPOSER_NAMES[str(proposer)],
                "env": payload["env"],
                "seed": int(cfg["seed"]),
                "horizon": int(cfg["horizon"]),
                "risk_quantile": float(cfg["risk_quantile"]),
                "checkpoint_tag": checkpoint_tag(str(payload["checkpoint"])),
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
                "accs_risk": float(accs["selected_false_certification"]),
                "accs_yield": float(accs["claim_yield"]),
                "accs_reward": float(accs["normalized_reward"]),
                "action_match_mean": float(test_diag.get("action_match_distance_mean", 0.0)),
                "action_match_median": float(test_diag.get("action_match_distance_median", 0.0)),
            }
        )
    return sorted(rows, key=lambda row: (row["proposer"], row["horizon"], row["seed"], row["file"]))


def write_csv(rows: List[Dict[str, object]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: List[Dict[str, object]], out_md: Path) -> None:
    groups: Dict[tuple, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[(row["proposer"], row["horizon"], row["risk_quantile"])].append(row)

    metric_cols = [
        "candidate_false",
        "top_false",
        "selection_gap",
        "global_risk",
        "global_yield",
        "reward_bin_risk",
        "reward_bin_yield",
        "crc_risk",
        "crc_yield",
        "accs_risk",
        "accs_yield",
        "accs_reward",
    ]
    lines = [
        "# Direct-OSRL Horizon Stress Summary",
        "",
        "| proposer | horizon | q | seeds | top F | global R/Y | reward-bin R/Y | CRC R/Y | ACCS R/Y |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key in sorted(groups):
        proposer, horizon, risk_q = key
        group = groups[key]
        def avg(col: str) -> float:
            return mean(float(row[col]) for row in group)

        lines.append(
            "| "
            + " | ".join(
                [
                    str(proposer),
                    str(horizon),
                    f"{risk_q:.2f}",
                    str(len(group)),
                    f"{100 * avg('top_false'):.2f}",
                    f"{100 * avg('global_risk'):.2f} / {100 * avg('global_yield'):.2f}",
                    f"{100 * avg('reward_bin_risk'):.2f} / {100 * avg('reward_bin_yield'):.2f}",
                    f"{100 * avg('crc_risk'):.2f} / {100 * avg('crc_yield'):.2f}",
                    f"{100 * avg('accs_risk'):.2f} / {100 * avg('accs_yield'):.2f}",
                ]
            )
            + " |"
        )

    lines.extend(["", "## Aggregate Metrics", ""])
    for key in sorted(groups):
        proposer, horizon, risk_q = key
        group = groups[key]
        lines.append(f"### {proposer} H={horizon} q={risk_q:.2f}")
        lines.append("")
        lines.append("| metric | mean | std |")
        lines.append("| --- | ---: | ---: |")
        for col in metric_cols:
            values = [float(row[col]) for row in group]
            lines.append(f"| {col} | {mean(values):.6f} | {pstdev(values):.6f} |")
        lines.append("")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pattern", action="append", default=None)
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "analysis" / "paper_assets" / "table_dsrl_horizon_stress.csv",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=ROOT / "outputs" / "phase_dsrl_horizon_stress_summary.md",
    )
    args = parser.parse_args()
    patterns = args.pattern or ["outputs/phase_dsrl_*_h*_modelbest_seed*_server.json"]
    rows = load_rows(patterns)
    if not rows:
        raise SystemExit("No horizon stress JSON files found.")
    write_csv(rows, args.out_csv)
    write_markdown(rows, args.out_md)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")


if __name__ == "__main__":
    main()
