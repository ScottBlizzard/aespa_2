"""Summarize episode-proxy audit JSON outputs."""

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


def load_rows(patterns: Iterable[str]) -> List[Dict[str, object]]:
    paths: List[Path] = []
    for pattern in patterns:
        paths.extend(sorted(ROOT.glob(pattern)))
        paths.extend(Path(p) for p in sorted(glob.glob(pattern)) if Path(p).is_absolute())
    rows: List[Dict[str, object]] = []
    seen = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen or not path.exists():
            continue
        seen.add(resolved)
        payload = json.loads(path.read_text(encoding="utf-8"))
        cfg = payload["config"]
        for method in payload["episode_proxy"]:
            rows.append(
                {
                    "file": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
                    "algo": payload["algo"],
                    "env": payload["env"],
                    "seed": int(cfg["seed"]),
                    "risk_quantile": float(cfg["risk_quantile"]),
                    "method": method["name"],
                    "block_risk": float(method["block_selected_false_certification"]),
                    "block_yield": float(method["block_claim_yield"]),
                    "block_realized_failure": float(method["block_realized_failure_rate"]),
                    "episode_risk": float(method["episode_false_certification"]),
                    "episode_yield": float(method["episode_claim_yield"]),
                    "episode_realized_failure": float(method["episode_realized_failure_rate"]),
                    "episode_count": int(method["episode_count"]),
                    "episode_issued": int(method["episode_issued"]),
                    "episode_failures": int(method["episode_failures"]),
                    "mean_issued_blocks_per_episode": float(method["mean_issued_blocks_per_episode"]),
                }
            )
    return sorted(rows, key=lambda row: (row["algo"], row["method"], row["seed"], row["file"]))


def write_csv(rows: List[Dict[str, object]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: List[Dict[str, object]], out_md: Path) -> None:
    groups: Dict[tuple, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[(row["algo"], row["method"])].append(row)

    base_methods = [
        "none_original_proposer",
        "global_candidate_cp",
        "reward_bin_ucb_20",
        "crc_style_safety_threshold",
        "accs_v0_support_safety",
        "episode_crc_safety_threshold",
        "episode_accs_support_safety",
    ]
    cap_methods = []
    for cap in [1, 2, 4, 8, 16]:
        cap_methods.extend(
            [
                f"none_original_proposer_episode_cap{cap}",
                f"global_candidate_cp_episode_cap{cap}",
                f"reward_bin_ucb_20_episode_cap{cap}",
                f"crc_style_safety_threshold_episode_cap{cap}",
                f"accs_v0_support_safety_episode_cap{cap}",
            ]
        )
    method_order = [
        *base_methods,
        *cap_methods,
        "oracle_residual_label",
    ]
    lines = [
        "# Episode-Proxy Audit Summary",
        "",
        "Values are percentages over logged test episodes grouped by anchor episode.",
        "This is not a closed-loop simulator guarantee.",
        "",
        "| algo | method | seeds | block R/Y | episode false/yield | realized episode fail | issued blocks/episode |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for algo in sorted({row["algo"] for row in rows}):
        for method in method_order:
            key = (algo, method)
            if key not in groups:
                continue
            items = groups[key]

            def avg(col: str) -> float:
                return mean(float(item[col]) for item in items)

            def std(col: str) -> float:
                return pstdev(float(item[col]) for item in items)

            lines.append(
                "| {algo} | {method} | {seeds} | {br:.2f}+/-{brs:.2f} / {by:.2f} | "
                "{er:.2f}+/-{ers:.2f} / {ey:.2f} | {rf:.2f}+/-{rfs:.2f} | {ib:.2f} |".format(
                    algo=algo,
                    method=method,
                    seeds=len(items),
                    br=100.0 * avg("block_risk"),
                    brs=100.0 * std("block_risk"),
                    by=100.0 * avg("block_yield"),
                    er=100.0 * avg("episode_risk"),
                    ers=100.0 * std("episode_risk"),
                    ey=100.0 * avg("episode_yield"),
                    rf=100.0 * avg("episode_realized_failure"),
                    rfs=100.0 * std("episode_realized_failure"),
                    ib=avg("mean_issued_blocks_per_episode"),
                )
            )
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pattern", action="append", default=None)
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "analysis" / "paper_assets" / "table_dsrl_episode_proxy_car_q92.csv",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=ROOT / "outputs" / "phase_dsrl_episode_proxy_car_q92_summary.md",
    )
    args = parser.parse_args()
    rows = load_rows(args.pattern or ["outputs/phase_dsrl_episode_proxy_*_car_q92_modelbest_seed*_server.json"])
    if not rows:
        raise SystemExit("No episode-proxy JSON files found.")
    write_csv(rows, args.out_csv)
    write_md(rows, args.out_md)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")


if __name__ == "__main__":
    main()
