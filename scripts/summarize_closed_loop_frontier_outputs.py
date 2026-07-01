"""Summarize fixed-cap closed-loop frontier JSON outputs by environment."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, Iterable, List


def load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def infer_seed(path: Path, payload: Dict) -> str:
    match = re.search(r"seed(\d+)", path.name)
    if match:
        return match.group(1)
    return str(payload.get("config", {}).get("seed", "unknown"))


def env_label(env_id: str) -> str:
    match = re.match(r"Offline(.+?)Circle-v0", env_id)
    return match.group(1) if match else env_id


def fmt_mean_std(values: List[float]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return f"{values[0]:.4f}"
    return f"{mean(values):.4f}+/-{stdev(values):.4f}"


def binomial_cdf_leq(k: int, n: int, p: float) -> float:
    if n <= 0:
        return 1.0
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0

    log_p = math.log(p)
    log_q = math.log1p(-p)
    log_terms = [
        math.lgamma(n + 1)
        - math.lgamma(i + 1)
        - math.lgamma(n - i + 1)
        + i * log_p
        + (n - i) * log_q
        for i in range(k + 1)
    ]
    max_log = max(log_terms)
    return min(1.0, math.exp(max_log) * sum(math.exp(term - max_log) for term in log_terms))


def clopper_pearson_upper(k: int, n: int, delta: float = 0.05) -> float:
    if n <= 0:
        return 1.0
    if k >= n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if binomial_cdf_leq(k, n, mid) >= delta:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def collect_rows(paths: Iterable[Path]) -> List[Dict]:
    rows: List[Dict] = []
    for path in sorted(paths):
        payload = load_json(path)
        config = payload["config"]
        algo = config["algo"]
        env_id = config["env_id"]
        seed = infer_seed(path, payload)
        test_summary = payload["test_summary"]
        for rule in payload["rules"]:
            audit = rule["audit"]
            test = rule["test"]
            rows.append(
                {
                    "env_id": env_id,
                    "env": env_label(env_id),
                    "algo": algo,
                    "seed": seed,
                    "cap": int(rule["cap"]),
                    "test_cost_mean": float(test_summary["cost_mean"]),
                    "test_violation_rate": float(test_summary["episode_violation_rate"]),
                    "audit_false_episodes": int(audit["false_episodes"]),
                    "audit_issued_episodes": int(audit["issued_episodes"]),
                    "test_false_episodes": int(test["false_episodes"]),
                    "test_issued_episodes": int(test["issued_episodes"]),
                    "test_episode_false": float(test["episode_false"]),
                    "test_episode_yield": float(test["episode_yield"]),
                    "test_block_risk": float(test["block_risk"]),
                    "test_block_yield": float(test["block_yield"]),
                    "issued_steps_per_episode": float(test["issued_steps_per_episode"]),
                    "source": str(path),
                }
            )
    return rows


def summarize(rows: List[Dict]) -> List[Dict]:
    groups: Dict[tuple, List[Dict]] = defaultdict(list)
    for row in rows:
        groups[(row["env_id"], row["algo"], row["cap"])].append(row)

    out: List[Dict] = []
    for (env_id, algo, cap), items in sorted(groups.items()):
        audit_false = sum(item["audit_false_episodes"] for item in items)
        audit_issued = sum(item["audit_issued_episodes"] for item in items)
        test_false = sum(item["test_false_episodes"] for item in items)
        test_issued = sum(item["test_issued_episodes"] for item in items)
        out.append(
            {
                "env_id": env_id,
                "env": env_label(env_id),
                "algo": algo,
                "cap": cap,
                "seeds": len({item["seed"] for item in items}),
                "audit_false_issued": f"{audit_false}/{audit_issued}",
                "audit_ep_cp90_upper": f"{clopper_pearson_upper(audit_false, audit_issued, 0.10):.4f}",
                "audit_ep_cp95_upper": f"{clopper_pearson_upper(audit_false, audit_issued, 0.05):.4f}",
                "test_cost_mean": fmt_mean_std([item["test_cost_mean"] for item in items]),
                "test_violation_rate": fmt_mean_std([item["test_violation_rate"] for item in items]),
                "test_false_issued": f"{test_false}/{test_issued}",
                "test_ep_cp90_upper": f"{clopper_pearson_upper(test_false, test_issued, 0.10):.4f}",
                "test_ep_cp95_upper": f"{clopper_pearson_upper(test_false, test_issued, 0.05):.4f}",
                "test_episode_false": fmt_mean_std([item["test_episode_false"] for item in items]),
                "test_episode_yield": fmt_mean_std([item["test_episode_yield"] for item in items]),
                "test_block_risk": fmt_mean_std([item["test_block_risk"] for item in items]),
                "test_block_yield": fmt_mean_std([item["test_block_yield"] for item in items]),
                "issued_steps_per_episode": fmt_mean_std([item["issued_steps_per_episode"] for item in items]),
            }
        )
    return out


def write_csv(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "env",
        "env_id",
        "algo",
        "cap",
        "seeds",
        "audit_false_issued",
        "audit_ep_cp90_upper",
        "audit_ep_cp95_upper",
        "test_cost_mean",
        "test_violation_rate",
        "test_false_issued",
        "test_ep_cp90_upper",
        "test_ep_cp95_upper",
        "test_episode_false",
        "test_episode_yield",
        "test_block_risk",
        "test_block_yield",
        "issued_steps_per_episode",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Closed-Loop Fixed-Cap Frontier Summary",
        "",
        "Rows aggregate independent online audit/test episodes across checkpoint seeds within each environment. CP90/CP95 are one-sided exact binomial upper bounds for the fixed first-cap rule.",
        "",
        "| env | algo | cap | seeds | audit false/issued | audit CP90/95 | test cost | violation | test false/issued | test CP90/95 | ep F/Y | block R/Y | issued steps/ep |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['env']} | {row['algo']} | {row['cap']} | {row['seeds']} | "
            f"{row['audit_false_issued']} | {row['audit_ep_cp90_upper']}/{row['audit_ep_cp95_upper']} | "
            f"{row['test_cost_mean']} | {row['test_violation_rate']} | "
            f"{row['test_false_issued']} | {row['test_ep_cp90_upper']}/{row['test_ep_cp95_upper']} | "
            f"{row['test_episode_false']} / {row['test_episode_yield']} | "
            f"{row['test_block_risk']} / {row['test_block_yield']} | "
            f"{row['issued_steps_per_episode']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = summarize(collect_rows(args.inputs))
    write_csv(args.out_csv, rows)
    write_markdown(args.out_md, rows)


if __name__ == "__main__":
    main()
