#!/usr/bin/env bash
set -euo pipefail

cd /workspace/thymic_project/paper/aaai_2
export PYTHONPATH=/workspace/thymic_project/paper/aaai_2/external/OSRL

device="${1:-cuda:1}"
mkdir -p outputs analysis/paper_assets

for model_reward_weight in 0.00 0.25 0.50; do
  for model_cost_weight in 0.00 0.25 0.50; do
    stem="phase_dsrl_capsiql_checkpoint_grid_q92_mrw${model_reward_weight}_mcw${model_cost_weight}"
    echo "RUN ${stem} device=${device}"
    .venv/bin/python src/run_dsrl_capsiql_checkpoint_pilot.py \
      --n-audit 4000 \
      --n-test 6000 \
      --k 64 \
      --neighbor-pool 512 \
      --risk-quantile 0.92 \
      --reward-risk-bonus 0.25 \
      --reward-support-bonus 0.10 \
      --model-reward-weight "${model_reward_weight}" \
      --model-cost-weight "${model_cost_weight}" \
      --device "${device}" \
      --no-query-bank \
      --out-json "outputs/${stem}_server.json" \
      --out-md "outputs/${stem}_server.md"
  done
done

.venv/bin/python - <<'PY'
import csv
import glob
import json
from pathlib import Path

rows = []
for path in sorted(glob.glob("outputs/phase_dsrl_capsiql_checkpoint_grid_q92_*.json")):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    auditors = {row["name"]: row for row in payload["auditors"]}
    accs = auditors["accs_v0_support_safety"]
    crc = auditors["crc_style_safety_threshold"]
    none = auditors["none_original_proposer"]
    diag = payload["diagnostics"]
    cfg = payload["config"]
    rows.append(
        {
            "path": path,
            "model_reward_weight": float(cfg["model_reward_weight"]),
            "model_cost_weight": float(cfg["model_cost_weight"]),
            "candidate_false": diag["test_candidate_false_rate"],
            "top_false": diag["test_top_reward_false_rate"],
            "selection_gap": diag["test_top_reward_false_rate"] - diag["test_candidate_false_rate"],
            "none_risk": none["selected_false_certification"],
            "none_yield": none["claim_yield"],
            "none_reward": none["normalized_reward"],
            "crc_risk": crc["selected_false_certification"],
            "crc_yield": crc["claim_yield"],
            "crc_reward": crc["normalized_reward"],
            "accs_risk": accs["selected_false_certification"],
            "accs_yield": accs["claim_yield"],
            "accs_reward": accs["normalized_reward"],
        }
    )

csv_path = Path("analysis/paper_assets/table_dsrl_capsiql_checkpoint_grid_q92.csv")
with csv_path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

cols = [
    "model_reward_weight",
    "model_cost_weight",
    "candidate_false",
    "top_false",
    "selection_gap",
    "crc_risk",
    "crc_yield",
    "crc_reward",
    "accs_risk",
    "accs_yield",
    "accs_reward",
]
lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
for row in rows:
    lines.append("| " + " | ".join(f"{row[col]:.6f}" for col in cols) + " |")
md_path = Path("outputs/phase_dsrl_capsiql_checkpoint_grid_q92_summary.md")
md_path.write_text("# CAPSIQL Checkpoint q0.92 Grid\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
Path("outputs/phase_dsrl_capsiql_checkpoint_grid_q92_summary.json").write_text(
    json.dumps(rows, indent=2),
    encoding="utf-8",
)
print(f"Wrote {csv_path}")
print(f"Wrote {md_path}")
PY
