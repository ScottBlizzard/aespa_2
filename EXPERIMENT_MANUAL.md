# 实验手册 (Experiment Manual)

> **用途**：防止上下文丢失时快速恢复实验环境、服务器路径和运行规范。每次新对话开始时优先阅读本文件。  
> **最后更新**：2026-06-24
> **项目**：AAAI_2 / ACCS, Action-Conditional Conformal Shields for Offline Safe RL  
> **当前状态**：本地 toy / hardened baseline / theory spine 已完成；A40 项目目录和项目本地 `.venv` 已配置并通过 smoke test；DSRL 官方 HDF5 数据已通过 Hugging Face 镜像下载并放到 A40 `data/dsrl/`。当前主线不再停留在 logged-neighbor bridge：CAPSIQL 50k q0.93 已完成三 seed trained-checkpoint 结果，CPQ 10k 与 COptiDICE 10k 都已完成三 seed direct OSRL baseline。详见 `experiment_report.md`、`analysis/dsrl_caps_integration_status.md`、`outputs/phase_dsrl_capsiql_checkpoint_50k_q93_summary.md`、`outputs/phase_dsrl_cpq_checkpoint_10k_q92_modelbest_summary.md`、`outputs/phase_dsrl_coptidice_checkpoint_10k_q92_modelbest_summary.md`。

---

## 一、角色分工

```text
本地 Windows: 代码编辑、分析、论文写作、smoke test、结果整理
4090 服务器: 多 seed、Safety-Gymnasium、DSRL 中等规模实验
A40 服务器: 大 batch、MetaDrive/复杂环境、重 baseline 或长时间运行
```

正式论文数字只允许来自：

```text
outputs/*_server.json
outputs/*_server.md
analysis/paper_assets/*
experiment_report.md 中列出的 canonical outputs
```

本地输出只能作为 `local smoke test`，不能直接进入摘要、引言或主表。

---

## 二、服务器信息

### 1. 4090 服务器（8x RTX 4090, 24GB/卡）

| 项目 | 值 |
|---|---|
| SSH 命令 | `ssh ccj@10.10.217.244` |
| 认证方式 | 免密（已配置密钥） |
| 内网要求 | 必须连接学校/实验室内网 |
| 项目路径 | `/home/ccj/workspace_1/aaai_2/` |
| 代码路径 | `/home/ccj/workspace_1/aaai_2/src/` |
| 输出路径 | `/home/ccj/workspace_1/aaai_2/outputs/` |
| 推荐环境 | `conda activate aaai2`；若未创建，先复用 PyTorch CUDA 环境后补依赖 |
| 主要用途 | toy 多 seed、Safety-Gymnasium、DSRL、ablation、group sweep |

标准启动流程：

```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate aaai2
cd /home/ccj/workspace_1/aaai_2/src
CUDA_VISIBLE_DEVICES=0 python <script>.py > ../outputs/log_<name>.txt 2>&1 &
```

GPU 检查：

```bash
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
```

### 2. A40 服务器（2x NVIDIA A40, 46GB/卡）

| 项目 | 值 |
|---|---|
| SSH 命令 | `ssh -p 10008 root@10.91.11.250` |
| 认证方式 | 免密（已配置密钥） |
| 内网要求 | 必须连接学校/实验室内网 |
| 项目路径 | `/workspace/thymic_project/paper/aaai_2/` |
| 代码路径 | `/workspace/thymic_project/paper/aaai_2/src/` |
| 输出路径 | `/workspace/thymic_project/paper/aaai_2/outputs/` |
| 推荐环境 | `conda activate aaai2` 或复用 `thymic_baseline` 后补依赖 |
| 主要用途 | 大规模 DSRL、MetaDrive、长 horizon audit、重 baseline |

标准启动流程：

```bash
cd /workspace/thymic_project/paper/aaai_2/src
../.venv/bin/python <script>.py > ../outputs/log_<name>.txt 2>&1 &
```

当前实际环境：

```text
project root: /workspace/thymic_project/paper/aaai_2/
python: /workspace/thymic_project/paper/aaai_2/.venv/bin/python
base used to create venv: /root/miniconda3/envs/thymic_baseline/bin/python
CUDA visible to torch: yes, 2 x NVIDIA A40
```

DSRL/Safety-Gymnasium 诊断环境：

```text
python: /workspace/thymic_project/paper/aaai_2/.venv310/bin/python
base python: Python 3.10.12
purpose: DSRL simulator reset/step and run_dsrl_env_pilot.py diagnostics
installed: dsrl==0.1.0, safety-gymnasium==0.4.0, gymnasium==0.28.1, gym==0.26.2,
           numpy==1.26.4, h5py, pandas, matplotlib, scikit-learn, scipy, tqdm
```

已在项目本地 `.venv` 中可导入：

```text
numpy==1.26.4
pandas==3.0.2
matplotlib
torch==2.6.0+cu124
gymnasium==0.28.1
gymnasium_robotics==1.2.2
mujoco==2.3.3
pygame==2.6.1
safety_gymnasium==1.0.0  # installed with --no-deps because pygame==2.1.0 has no wheel here
dsrl==0.1.0              # installed with --no-deps
xmltodict
```

注意：

- 不要改 `thymic_baseline`，后续依赖只装进 `/workspace/thymic_project/paper/aaai_2/.venv`。
- `safety-gymnasium` 的官方依赖 pin `pygame==2.1.0`，Python 3.11 下会尝试编译并缺 `sdl2-config`；当前用 `pygame==2.6.1` + `safety-gymnasium --no-deps` 绕开。
- 第一个 synthetic OSRL-style pilot 已完成；CAPSIQL 与 CPQ checkpoint evaluator 已跑通，COptiDICE training smoke 已跑通。
- Python 3.11 `.venv` 下的 Safety-Gymnasium 真实导入会触发 dataclass mutable-default 问题；DSRL 诊断统一用 `.venv310`。
- 旧 `data.offline-saferl.org` endpoint 当前不可达；当前 DSRL GitHub 使用 Hugging Face HDF5。A40 不能直连 `huggingface.co` 入口时，从本地下载后 scp 到 `data/dsrl/`。
- 不要把 DSRL 自生成 query-bank 作为主实验证据；它只是排障和数据通路验证。CarCircle CAPS-style budget-head query-bank 可以作为 official-data bridge，但论文主线应优先使用 CAPSIQL/CPQ/COptiDICE 等 trained checkpoint under fixed query-bank/auditor contract。

DSRL 官方数据地址示例：

```text
https://huggingface.co/datasets/YYY-45/DSRL/resolve/main/SafetyCarCircle-v0-100-1450.hdf5
https://huggingface.co/datasets/YYY-45/DSRL/resolve/main/SafetyBallCircle-v0-80-886.hdf5
https://huggingface.co/datasets/YYY-45/DSRL/resolve/main/SafetyDroneCircle-v0-100-1923.hdf5
```

A40 数据路径：

```text
/workspace/thymic_project/paper/aaai_2/data/dsrl/
```

---

## 三、本地环境

| 项目 | 值 |
|---|---|
| 本地根目录 | `D:\AAAI_2` |
| 代码路径 | `D:\AAAI_2\src\` |
| 输出路径 | `D:\AAAI_2\outputs\` |
| 论文目录 | `D:\AAAI_2\aaai2027\` |
| 相关论文 | `D:\AAAI_2\papers\` |
| 主蓝图 | `D:\AAAI_2\idea_blueprint.md` |
| 实验报告 | `D:\AAAI_2\experiment_report.md` |
| 理论文档 | `D:\AAAI_2\theory_proofs.md` |

同步到 4090：

```powershell
.\push.ps1
```

同步到 A40：

```powershell
.\push.ps1 -Target a40
```

`push.ps1` 会自动创建：

```text
/workspace/thymic_project/paper/aaai_2/{src,scripts,outputs,analysis/paper_assets}
```

并只同步实验代码 `src/` 和 `scripts/`。服务器只作为实验执行环境：
保留代码、依赖、数据、`outputs/` 实验产物，以及脚本生成的
`analysis/paper_assets/*.csv` 汇总表；不要同步 `aaai2027/`、本地 paper、
根目录工作流 Markdown、`analysis/*.md` 或渲染检查图到服务器。

下载服务器输出：

```powershell
.\pull_outputs.ps1
.\pull_outputs.ps1 -Target a40
```

单文件上传：

```powershell
scp D:\AAAI_2\src\<file>.py ccj@10.10.217.244:/home/ccj/workspace_1/aaai_2/src/
scp -P 10008 D:\AAAI_2\src\<file>.py root@10.91.11.250:/workspace/thymic_project/paper/aaai_2/src/
```

PowerShell 注意事项：

- 不支持 Bash 风格 `&&`，用 `;` 或拆成多条命令。
- SSH 内嵌 Python 代码引号容易出错，复杂逻辑写成 `.py` 文件上传。
- 不要把实验输出放进 `src/`。

---

## 四、建议依赖

### 基础依赖

| 包 | 用途 |
|---|---|
| `torch` | cost/reward critic、offline policy、ensemble |
| `numpy`, `scipy` | 数据、统计、conformal quantile |
| `pandas` | 实验表格 |
| `matplotlib`, `seaborn` | 论文图 |
| `scikit-learn` | clustering、calibration diagnostics、simple baselines |
| `gymnasium` | RL 环境接口 |

### 环境/benchmark 依赖

| 包 | 用途 |
|---|---|
| `safety-gymnasium` | 主实验环境 |
| `dsrl` | offline safe RL benchmark |
| `d4rl` | 若 DSRL/旧数据需要 |
| `metadrive-simulator` | driving case study，可选 |
| `tianshou` / `stable-baselines3` | baseline policy 或 evaluation utilities，可选 |

---

## 五、代码架构规划

| 文件/目录 | 功能 |
|---|---|
| `src/config.py` | path、seed、budget、environment、calibration config |
| `src/data_io.py` | JSON/JSONL/CSV read-write helpers |
| `src/toy_env.py` | moving-budget gridworld / navigation toy |
| `src/offline_data.py` | offline trajectory split: train/calibration/test |
| `src/cost_model.py` | cost-return critic / ensemble / quantile predictor |
| `src/action_groups.py` | discrete bucket、cluster、risk embedding groups |
| `src/conformal.py` | conformal scores, quantiles, hierarchical fallback |
| `src/shield.py` | ACCS action filter, replacement, abstention |
| `src/eval_metrics.py` | U/C/A/H metrics |
| `src/baselines.py` | no shield, global conformal, state-only, pessimism |
| `src/run_phase1_toy.py` | toy main phenomenon |
| `src/run_phase2_accs.py` | ACCS prototype |
| `src/run_phase3_safety_gym.py` | Safety-Gymnasium main |
| `src/run_phase4_dsrl.py` | DSRL benchmark |
| `src/run_strong_proposer_pilot.py` | synthetic OSRL-style fixed query-bank pilot |
| `src/run_dsrl_env_pilot.py` | DSRL simulator query-bank diagnostic; not paper evidence yet |
| `src/run_dsrl_dataset_pilot.py` | official DSRL HDF5 logged-neighbor diagnostic; not paper evidence yet |
| `src/plot_paper_figures.py` | paper figures and tables |

---

## 六、实验阶段规划

| Phase | 目标 | Canonical 输出 |
|---|---|---|
| Phase 0 | protocol freeze, split, report schema | `outputs/phase0_protocol_freeze_server.json` |
| Phase 0.5 | synthetic strong-proposer query-bank pilot | `outputs/phase_strong_proposer_pilot_server.json` |
| Phase 1 | toy moving-budget main phenomenon | `outputs/phase1_toy_moving_budget_server.json` |
| Phase 2 | ACCS prototype and group-wise coverage | `outputs/phase2_accs_prototype_server.json` |
| Phase 3 | Safety-Gymnasium main comparison | `outputs/phase3_safety_gym_main_server.json` |
| Phase 4 | DSRL benchmark and strong baselines | `outputs/phase4_dsrl_main_server.json` |
| Phase 5 | distribution shift / recalibration audit | `outputs/phase5_shift_audit_server.json` |
| Phase 6 | horizon risk allocation audit | `outputs/phase6_horizon_audit_server.json` |
| Phase 7 | paper assets | `analysis/paper_assets/*` |

---

## 七、首批服务器命令模板

### A40 smoke test

```bash
cd /workspace/thymic_project/paper/aaai_2
.venv/bin/python -m py_compile \
  src/eval_metrics.py \
  src/selective_auditor.py \
  src/toy_selection_failure.py \
  src/toy_selection_failure_hardened.py \
  src/toy_policy_mismatch.py \
  src/toy_no_overlap.py

.venv/bin/python src/toy_selection_failure.py > outputs/log_a40_toy_selection_failure.txt 2>&1
.venv/bin/python src/toy_selection_failure_hardened.py > outputs/log_a40_toy_selection_failure_hardened.txt 2>&1
.venv/bin/python src/toy_policy_mismatch.py > outputs/log_a40_toy_policy_mismatch.txt 2>&1
.venv/bin/python src/toy_no_overlap.py > outputs/log_a40_toy_no_overlap.txt 2>&1
```

Synthetic strong-proposer pilot（已跑通）：
```bash
cd /workspace/thymic_project/paper/aaai_2
.venv/bin/python src/run_strong_proposer_pilot.py \
  > outputs/log_phase_strong_proposer_pilot_server.txt 2>&1
```

Canonical outputs:
```text
outputs/phase_strong_proposer_pilot_server.json
outputs/phase_strong_proposer_pilot_server.md
outputs/phase_strong_proposer_query_bank_server.npz
```

DSRL simulator diagnostic（负结果/排障用，不是 canonical paper result）：

```bash
cd /workspace/thymic_project/paper/aaai_2
.venv310/bin/python src/run_dsrl_env_pilot.py \
  > outputs/log_phase_dsrl_env_pilot_server.txt 2>&1
```

相关诊断文件：

```text
analysis/dsrl_caps_integration_status.md
outputs/phase_dsrl_env_pilot_*.json
outputs/log_phase_dsrl_env_pilot_*.txt
```

Official DSRL HDF5 logged-neighbor diagnostic（负结果/排障用，不是 canonical paper result）：

```bash
cd /workspace/thymic_project/paper/aaai_2
.venv310/bin/python src/run_dsrl_dataset_pilot.py \
  --env-id OfflineCarCircle-v0 \
  --n-audit 1200 \
  --n-test 2500 \
  --neighbor-pool 96 \
  --no-query-bank \
  > outputs/log_phase_dsrl_dataset_pilot_car_smoke.txt 2>&1
```

Trained CAPSIQL checkpoint evaluator（当前主线 trained proposer）：

```bash
cd /workspace/thymic_project/paper/aaai_2
PYTHONPATH=/workspace/thymic_project/paper/aaai_2/external/OSRL \
.venv/bin/python src/run_dsrl_capsiql_checkpoint_pilot.py \
  --checkpoint outputs/capsiql_car_logs_50k_5/OfflineCarCircle-v0/<run>/<run>/checkpoint/model.pt \
  --risk-quantile 0.93 \
  --reward-risk-bonus 0.00 \
  --model-reward-weight 1.00 \
  --model-cost-weight 0.00 \
  --no-query-bank \
  > outputs/log_capsiql_checkpoint_eval.txt 2>&1
```

Trained CPQ checkpoint evaluator（第一条 direct OSRL baseline）：

```bash
cd /workspace/thymic_project/paper/aaai_2
PYTHONPATH=/workspace/thymic_project/paper/aaai_2/external/OSRL \
.venv/bin/python src/run_dsrl_cpq_checkpoint_pilot.py \
  --checkpoint outputs/cpq_car_logs_10k/OfflineCarCircle-v0/<run>/<run>/checkpoint/model_best.pt \
  --risk-quantile 0.92 \
  --proposal-samples 96 \
  --no-query-bank \
  > outputs/log_cpq_checkpoint_eval.txt 2>&1
```

Trained COptiDICE checkpoint evaluator（第二条 direct OSRL baseline）：

```bash
cd /workspace/thymic_project/paper/aaai_2
PYTHONPATH=/workspace/thymic_project/paper/aaai_2/external/OSRL \
.venv/bin/python src/run_dsrl_coptidice_checkpoint_pilot.py \
  --checkpoint outputs/coptidice_car_logs_10k/OfflineCarCircle-v0/<run>/<run>/checkpoint/model_best.pt \
  --risk-quantile 0.92 \
  --proposal-samples 96 \
  --no-query-bank \
  > outputs/log_coptidice_checkpoint_eval.txt 2>&1
```

Canonical trained-checkpoint outputs:

```text
outputs/phase_dsrl_capsiql_checkpoint_50k_q93_summary.md
analysis/paper_assets/table_dsrl_capsiql_checkpoint_50k_q93_seeds.csv
outputs/phase_dsrl_cpq_checkpoint_10k_q92_modelbest_summary.md
analysis/paper_assets/table_dsrl_cpq_checkpoint_10k_q92_modelbest_seeds.csv
outputs/phase_dsrl_cpq_checkpoint_10k_q93_modelbest_summary.md
analysis/paper_assets/table_dsrl_cpq_checkpoint_10k_q93_modelbest_seeds.csv
outputs/phase_dsrl_coptidice_checkpoint_10k_q92_modelbest_summary.md
analysis/paper_assets/table_dsrl_coptidice_checkpoint_10k_q92_modelbest_seeds.csv
outputs/phase_dsrl_coptidice_checkpoint_10k_q93_modelbest_summary.md
analysis/paper_assets/table_dsrl_coptidice_checkpoint_10k_q93_modelbest_seeds.csv
```

Phase 1 toy：

```bash
cd /home/ccj/workspace_1/aaai_2/src
source ~/miniconda3/etc/profile.d/conda.sh
conda activate aaai2
python run_phase1_toy.py \
  --seeds 0,1,2,3,4 \
  --train-budgets 10,20 \
  --test-budgets 3,5,8,10,15,25 \
  --out ../outputs/phase1_toy_moving_budget_server.json \
  > ../outputs/log_phase1_toy_moving_budget.txt 2>&1 &
```

Phase 2 ACCS prototype：

```bash
cd /home/ccj/workspace_1/aaai_2/src
source ~/miniconda3/etc/profile.d/conda.sh
conda activate aaai2
python run_phase2_accs.py \
  --dataset ../outputs/phase1_toy_dataset.json \
  --group-modes global,state,action,state_action \
  --alphas 0.05,0.1 \
  --out ../outputs/phase2_accs_prototype_server.json \
  > ../outputs/log_phase2_accs_prototype.txt 2>&1 &
```

These commands are placeholders until scripts exist. Update this section after implementation.

---

## 八、常见问题排查

| 问题 | 原因 | 解决 |
|---|---|---|
| `python: command not found` | conda 未激活 | source conda 后 activate |
| `ModuleNotFoundError: safety_gymnasium` | 环境缺依赖 | 安装或先跑 toy |
| `CUDA out of memory` | batch 太大/GPU 被占 | 降 batch、换 GPU、先跑 CPU toy |
| coverage 过低 | calibration split 太小或 group 太细 | 查 group `n_calib`，启用 hierarchy |
| global conformal 看起来也很好 | toy 不够异质 | 加 action-specific risk structure |
| ACCS reward 崩 | fallback/abstention 过多 | 查 safe action set size 和 group radius |
| horizon violation 高 | policy-induced shift | 降理论 claim，做 shift audit / recalibration |
