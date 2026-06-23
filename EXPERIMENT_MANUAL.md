# 实验手册 (Experiment Manual)

> **用途**：防止上下文丢失时快速恢复实验环境、服务器路径和运行规范。每次新对话开始时优先阅读本文件。  
> **最后更新**：2026-06-23  
> **项目**：AAAI_2 / ACCS, Action-Conditional Conformal Shields for Offline Safe RL  
> **当前状态**：项目骨架已建立；正式实验尚未开始。短期目标是先跑 moving-budget toy main phenomenon，再上 Safety-Gymnasium / DSRL。

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
source /root/miniconda3/etc/profile.d/conda.sh
conda activate aaai2
cd /workspace/thymic_project/paper/aaai_2/src
CUDA_VISIBLE_DEVICES=0 python <script>.py > ../outputs/log_<name>.txt 2>&1 &
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
| `src/plot_paper_figures.py` | paper figures and tables |

---

## 六、实验阶段规划

| Phase | 目标 | Canonical 输出 |
|---|---|---|
| Phase 0 | protocol freeze, split, report schema | `outputs/phase0_protocol_freeze_server.json` |
| Phase 1 | toy moving-budget main phenomenon | `outputs/phase1_toy_moving_budget_server.json` |
| Phase 2 | ACCS prototype and group-wise coverage | `outputs/phase2_accs_prototype_server.json` |
| Phase 3 | Safety-Gymnasium main comparison | `outputs/phase3_safety_gym_main_server.json` |
| Phase 4 | DSRL benchmark and strong baselines | `outputs/phase4_dsrl_main_server.json` |
| Phase 5 | distribution shift / recalibration audit | `outputs/phase5_shift_audit_server.json` |
| Phase 6 | horizon risk allocation audit | `outputs/phase6_horizon_audit_server.json` |
| Phase 7 | paper assets | `analysis/paper_assets/*` |

---

## 七、首批服务器命令模板

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

