#!/usr/bin/env bash
set -u

cd /workspace/thymic_project/paper/aaai_2 || exit 1

for env_id in OfflineBallCircle-v0 OfflineCarCircle-v0 OfflineDroneCircle-v0; do
  for bonus in 0.0 0.5 1.0 1.5; do
    safe_env="${env_id//-/_}"
    safe_env="${safe_env//./_}"
    safe_bonus="${bonus//./p}"
    echo "START env=${env_id} bonus=${bonus}"
    .venv310/bin/python src/run_dsrl_dataset_pilot.py \
      --env-id "${env_id}" \
      --n-audit 1200 \
      --n-test 2500 \
      --neighbor-pool 128 \
      --reward-risk-bonus "${bonus}" \
      --reward-support-bonus 0.10 \
      --no-query-bank \
      --out-json "outputs/phase_dsrl_dataset_sweep_${safe_env}_risk${safe_bonus}.json" \
      --out-md "outputs/phase_dsrl_dataset_sweep_${safe_env}_risk${safe_bonus}.md"
    echo "DONE env=${env_id} bonus=${bonus}"
  done
done
