#!/usr/bin/env bash
set -u

cd /workspace/thymic_project/paper/aaai_2 || exit 1

env_id="OfflineCarCircle-v0"
for risk_q in 0.92 0.93 0.94; do
  for risk_bonus in 0.25 0.5 0.75; do
    for support_bonus in 0.00 0.10; do
      alpha="0.05"
      gamma="0.05"
      safe_q="${risk_q//./p}"
      safe_risk_bonus="${risk_bonus//./p}"
      safe_support_bonus="${support_bonus//./p}"
      safe_alpha="${alpha//./p}"
      safe_gamma="${gamma//./p}"
      echo "START env=${env_id} q=${risk_q} risk_bonus=${risk_bonus} support_bonus=${support_bonus} alpha=${alpha} gamma=${gamma}"
      .venv310/bin/python src/run_dsrl_dataset_pilot.py \
        --env-id "${env_id}" \
        --k 64 \
        --n-audit 9000 \
        --n-test 12000 \
        --neighbor-pool 384 \
        --proposer-mode budget_heads \
        --budget-lambdas=-0.5,0.0,0.25,0.5,1.0,2.0,4.0,8.0 \
        --risk-quantile "${risk_q}" \
        --reward-risk-bonus "${risk_bonus}" \
        --reward-support-bonus "${support_bonus}" \
        --alpha "${alpha}" \
        --gamma "${gamma}" \
        --no-query-bank \
        --out-json "outputs/phase_dsrl_car_capsstyle_grid_q${safe_q}_risk${safe_risk_bonus}_support${safe_support_bonus}_alpha${safe_alpha}_gamma${safe_gamma}.json" \
        --out-md "outputs/phase_dsrl_car_capsstyle_grid_q${safe_q}_risk${safe_risk_bonus}_support${safe_support_bonus}_alpha${safe_alpha}_gamma${safe_gamma}.md"
      echo "DONE env=${env_id} q=${risk_q} risk_bonus=${risk_bonus} support_bonus=${support_bonus} alpha=${alpha} gamma=${gamma}"
    done
  done
done
