#!/usr/bin/env bash
set -u

ROOT="${ROOT:-/home/ccj/workspace_1/aaai_2}"
CONDA_ENV="${CONDA_ENV:-aaai2}"
RUN_ID="${RUN_ID:-tuned_rule_100x200x200_20260630_4090}"
TUNE_EPISODES="${TUNE_EPISODES:-100}"
AUDIT_EPISODES="${AUDIT_EPISODES:-200}"
TEST_EPISODES="${TEST_EPISODES:-200}"
CAPS="${CAPS:-16,32,64,128,256,512}"
WINDOWS="${WINDOWS:-all,early,mid}"
SCORE_QUANTILES="${SCORE_QUANTILES:-0.05,0.10,0.20,0.35,0.50,0.65,0.80}"
ALPHA_EP="${ALPHA_EP:-0.05}"
MIN_EPISODE_YIELD="${MIN_EPISODE_YIELD:-0.10}"
MAX_PARALLEL="${MAX_PARALLEL:-8}"
NUM_GPUS="${NUM_GPUS:-8}"
SEEDS="${SEEDS:-20260624 20260625 20260626}"
ENV_SHORTS="${ENV_SHORTS:-car ball drone}"
ALGOS="${ALGOS:-cpq coptidice}"

cd "$ROOT" || exit 1
source ~/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

export PYGAME_HIDE_SUPPORT_PROMPT="${PYGAME_HIDE_SUPPORT_PROMPT:-1}"
export MUJOCO_GL="${MUJOCO_GL:-egl}"
export WANDB_MODE="${WANDB_MODE:-offline}"
export PYTHONPATH="$ROOT/src:$ROOT/external/OSRL:${PYTHONPATH:-}"

mkdir -p outputs analysis/paper_assets
LOG_DIR="outputs/${RUN_ID}_logs"
mkdir -p "$LOG_DIR"
DRIVER_LOG="$LOG_DIR/driver_status.tsv"
printf "time\tstatus\tgpu\talgo\tenv\tseed\toutput\n" > "$DRIVER_LOG"

env_id_for() {
  case "$1" in
    car) echo "OfflineCarCircle-v0" ;;
    ball) echo "OfflineBallCircle-v0" ;;
    drone) echo "OfflineDroneCircle-v0" ;;
    *) echo "unknown env short: $1" >&2; return 1 ;;
  esac
}

env_dir_for() {
  case "$1" in
    car) echo "OfflineCarCircle-v0-cost-20" ;;
    ball) echo "OfflineBallCircle-v0-cost-20" ;;
    drone) echo "OfflineDroneCircle-v0-cost-20" ;;
    *) echo "unknown env short: $1" >&2; return 1 ;;
  esac
}

checkpoint_for() {
  local algo="$1"
  local env_short="$2"
  local seed="$3"
  local env_dir
  env_dir="$(env_dir_for "$env_short")" || return 1
  echo "outputs/${algo}_${env_short}_logs_10k/${env_dir}/${algo}_${env_short}_10k_seed${seed}/${algo}_${env_short}_10k_seed${seed}/checkpoint/model_best.pt"
}

run_one() {
  local gpu="$1"
  local algo="$2"
  local env_short="$3"
  local seed="$4"
  local env_id
  local checkpoint
  local stem
  local output
  local log

  env_id="$(env_id_for "$env_short")" || return 1
  checkpoint="$(checkpoint_for "$algo" "$env_short" "$seed")" || return 1
  stem="phase_dsrl_closed_loop_tuned_rule_${RUN_ID}_${algo}_${env_short}_seed${seed}_${TUNE_EPISODES}x${AUDIT_EPISODES}x${TEST_EPISODES}_server"
  output="outputs/${stem}.json"
  log="$LOG_DIR/${stem}.log"

  printf "%s\tstart\t%s\t%s\t%s\t%s\t%s\n" "$(date -Iseconds)" "$gpu" "$algo" "$env_short" "$seed" "$output" >> "$DRIVER_LOG"
  (
    set -euo pipefail
    echo "START $(date -Iseconds) gpu=$gpu algo=$algo env=$env_id seed=$seed"
    echo "checkpoint=$checkpoint"
    nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader
    CUDA_VISIBLE_DEVICES="$gpu" python src/run_dsrl_closed_loop_tuned_rule_audit.py \
      --algo "$algo" \
      --env-id "$env_id" \
      --checkpoint "$checkpoint" \
      --seed "$seed" \
      --tune-episodes "$TUNE_EPISODES" \
      --audit-episodes "$AUDIT_EPISODES" \
      --test-episodes "$TEST_EPISODES" \
      --caps "$CAPS" \
      --windows "$WINDOWS" \
      --score-quantiles "$SCORE_QUANTILES" \
      --alpha-ep "$ALPHA_EP" \
      --min-episode-yield "$MIN_EPISODE_YIELD" \
      --device cuda:0 \
      --output "$output"
    echo "DONE $(date -Iseconds) output=$output"
  ) > "$log" 2>&1
  local status=$?
  if [ "$status" -eq 0 ]; then
    printf "%s\tdone\t%s\t%s\t%s\t%s\t%s\n" "$(date -Iseconds)" "$gpu" "$algo" "$env_short" "$seed" "$output" >> "$DRIVER_LOG"
  else
    printf "%s\tfail:%s\t%s\t%s\t%s\t%s\t%s\n" "$(date -Iseconds)" "$status" "$gpu" "$algo" "$env_short" "$seed" "$output" >> "$DRIVER_LOG"
  fi
  return "$status"
}

PIDS=()
JOB_INDEX=0
FAILED=0

wait_group() {
  local pid
  local group_failed=0
  for pid in "${PIDS[@]}"; do
    if ! wait "$pid"; then
      group_failed=1
    fi
  done
  PIDS=()
  if [ "$group_failed" -ne 0 ]; then
    FAILED=1
  fi
}

launch() {
  local algo="$1"
  local env_short="$2"
  local seed="$3"
  local gpu=$((JOB_INDEX % NUM_GPUS))
  JOB_INDEX=$((JOB_INDEX + 1))
  run_one "$gpu" "$algo" "$env_short" "$seed" &
  PIDS+=("$!")
  if [ "${#PIDS[@]}" -ge "$MAX_PARALLEL" ]; then
    wait_group
  fi
}

echo "RUN_ID=$RUN_ID"
echo "TUNE_EPISODES=$TUNE_EPISODES AUDIT_EPISODES=$AUDIT_EPISODES TEST_EPISODES=$TEST_EPISODES"
echo "CAPS=$CAPS WINDOWS=$WINDOWS SCORE_QUANTILES=$SCORE_QUANTILES ALPHA_EP=$ALPHA_EP MIN_EPISODE_YIELD=$MIN_EPISODE_YIELD"
echo "SEEDS=$SEEDS ENV_SHORTS=$ENV_SHORTS ALGOS=$ALGOS MAX_PARALLEL=$MAX_PARALLEL NUM_GPUS=$NUM_GPUS"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader

for seed in $SEEDS; do
  for env_short in $ENV_SHORTS; do
    for algo in $ALGOS; do
      launch "$algo" "$env_short" "$seed"
    done
  done
done

wait_group

if [ "$FAILED" -ne 0 ]; then
  echo "At least one tuned-rule job failed. See $LOG_DIR." >&2
  exit 1
fi

python scripts/summarize_closed_loop_tuned_rule_outputs.py \
  outputs/phase_dsrl_closed_loop_tuned_rule_${RUN_ID}_*_server.json \
  --out-csv "analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_${RUN_ID}.csv" \
  --out-md "outputs/phase_dsrl_closed_loop_tuned_rule_${RUN_ID}_summary.md"

echo "SUMMARY outputs/phase_dsrl_closed_loop_tuned_rule_${RUN_ID}_summary.md"
echo "CSV analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_${RUN_ID}.csv"
