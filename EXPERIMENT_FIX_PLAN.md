# 实验修正计划 (Experiment Fix Plan)

> **最后更新**：2026-06-23  
> **用途**：记录失败实验的诊断与修复路线。不要把坏结果删除；把它们分成 bug / artifact、真实 insight、boundary condition。

---

## 0. 当前状态

正式实验尚未开始。本文件先记录 `AAAI_2` 最可能遇到的失败模式，避免实验失败后临时改叙事。

核心论文目标：

```text
Fixed-budget safe RL performance is not deployment safety evidence.
ACCS turns safety into calibrated, budget-conditioned, action-level claims.
```

---

## 1. 坏结果分流规则

| 类别 | 判定标准 | 处理 |
|---|---|---|
| Bug / artifact | 修正 split、seed、budget、代码、环境后消失 | 修，不写成 insight |
| True insight | 多 seed、多环境、baseline 后仍稳定 | 提炼为主发现或边界 |
| Boundary condition | 真实存在但只在特定环境/shift/group 下成立 | 写成 limitation 或 diagnostic |

所有分流必须写进 `experiment_report.md` 或本文件。

---

## 2. 高风险问题与修复路线

### 风险 1: Toy 主现象不够强

症状：

- no-shield 在 stricter budget 下没有明显 violation；
- global conformal 不比 ACCS 更保守；
- action groups 没有风险异质性。

修复：

1. 明确加入 action-specific cost structure，例如 high-speed/turn actions 风险更高。
2. 让 train budget `{10,20}` 与 test budget `{3,5}` 有足够差距。
3. 设计 rare hazard cells，使 fixed-budget policy 容易学到 aggressive action。
4. 保持 toy 简单，目标是证明主现象，不是 benchmark。

### 风险 2: ACCS 被 global conformal 打平

症状：

- global shield 与 action-conditional shield reward/violation 接近。

修复：

1. 检查 action group 内 residual variance 是否真的更小。
2. 增加 heterogeneous actions：低风险动作和高风险动作 residual 分布要明显不同。
3. 报 safe action set size；global 可能 violation 相同但 action set 更小。
4. 用 matched violation frontier，不只报单点。

### 风险 3: action groups 太稀疏导致 abstention 太多

症状：

- `n_calib < n_min` 的 group 太多；
- reward 主要被 abstention/fallback 拉低。

修复：

1. 启用 hierarchy: state-action -> action -> risk cluster -> global。
2. 报 abstention reason breakdown。
3. 做 granularity sweep，把稀疏性写成 tradeoff。
4. 如果连续动作太难，先在离散/离散化动作空间建立主现象。

### 风险 4: action-level coverage 无法转化为 episode safety

症状：

- per-action coverage 够，但 episode violation 高。

处理：

1. 不把它包装成失败；这正是 `C does not imply H` 的证据。
2. 加 risk allocation、residual budget 和 horizon audit。
3. 报 coverage degradation over time。
4. 用 online recalibration 或 shift-triggered abstention 作为 mitigation，不当作 theorem。

### 风险 5: offline safe RL baselines 太强

症状：

- CQL-Lagrangian/CPQ/COptiDICE 在所有 budgets 下表现很好。

修复：

1. 明确区分 seen budgets 和 unseen budgets。
2. 加 retrain-per-budget 作为 expensive upper bound，而不是直接敌人。
3. 强调 ACCS 是 plug-in / retrain-free / calibrated action report。
4. 报 adaptation latency 和 calibration report，而不仅是 reward。

### 风险 6: reviewer 认为只是 conformal prediction

症状：

- 方法看起来像 `Q_c + quantile`。

修复写法：

1. 主线必须从 moving constraints 和 action-safety claim 开始。
2. 把 global/state/action conditional baselines 做全。
3. 强调 hierarchy/abstention/report schema。
4. 用 `U/C/A/H` claim-evidence map 支撑，而不是只讲公式。

---

## 3. 优先修正队列

### P0: Protocol leakage audit

检查：

- training/calibration/test split；
- action grouping 是否在 test 上调过；
- budget list 是否泄漏；
- quantile 是否按 finite-sample conformal 公式；
- seeds 是否固定记录。

### P1: Main phenomenon rescue

如果 Phase 1 不干净，优先修 toy，不急着上 Safety-Gym。

Go 标准：

```text
no shield: high reward but violates stricter unseen budgets
global conformal: low violation but visibly over-conservative
ACCS: better reward at matched violation / coverage
```

### P2: Coverage diagnostic rescue

如果 coverage 不稳定：

- 检查 group residual distribution；
- 增加 calibration size；
- 使用 normalized nonconformity；
- 用 hierarchical groups；
- report undercoverage groups honestly。

---

## 4. 写作保护线

不管实验好坏，以下边界不能破：

1. 不声称 full safe RL guarantee。
2. 不声称 conformal 在 policy shift 下自动有效。
3. 不把 abstention 写成失败。
4. 不隐藏 sparse groups。
5. 不把 repaired/fallback action 当作 raw policy ability。
6. 不把 episode-level metrics 当 action-level theorem 证明。

