# AAAI_2 Oral Blueprint: Calibration After Action Selection

> **版本**：2026-06-23  
> **目标会议**：AAAI 2027 / trustworthy RL / safe decision making  
> **当前定位**：这不应写成“offline safe RL + conformal prediction”的自然组合，也不应写成“比 CAPS 更会适配 budget 的 policy”。升级后的唯一主线是 **calibration after deployment-time action selection**：已有方法会用 learned cost / feasibility score 选择动作，但这些 score 在有限离线数据下经过 action selection 后可能把错误集中到真正执行的动作上。ACCS 必须成为 selection-aware finite-data auditor，而不是泛泛的 shield。

---

## 0A. Oral 级升级后的唯一主线

Phase 0 文献调研已经确认：`CAPS`、`TREBI`、`AEGIS`、`BCRL`、`SafeFQL` 已经覆盖了大量 “changing / real-time / any-budget safe offline RL” 和 action-feasibility 空间。因此 AAAI_2 不能再把新颖性押在：

```text
offline safe RL can adapt to new budgets without retraining
```

升级后的主问题必须是：

```text
After a deployment system selects an action from learned safe-RL scores,
is the issued safety certificate still calibrated on the selected actions?
```

论文灵魂从 “better shield” 升级为：

```text
A learned cost or feasibility estimate is not a calibrated deployment certificate.
```

更精确地说：

```text
Existing budget-adaptive offline safe-RL methods select actions by thresholding
learned cost or feasibility scores. Under finite offline data, selection can
concentrate score errors precisely among the actions that are executed.
```

ACCS 的身份也随之升级：

```text
ACCS is a selection-aware action auditor:
it controls or diagnoses false certification among issued action claims
for a declared proposal stream, budget query rule, and continuation policy.
```

这给本文一个区别于 CAPS/BCRL/AEGIS 的干净边界：

| Existing line | What it already does | What remains open |
|---|---|---|
| CAPS | action filtering and policy switching under varying constraints | finite-data calibration after selected-action filtering |
| BCRL | budget-conditioned persistent safe sets | false certification control under finite samples and selected queries |
| AEGIS | feasible-budget action/policy structure | post-selection calibration of learned feasibility scores |
| SafeFQL | conformal calibration of a learned safety boundary | selected-action false-certification control under moving budgets/base scores |
| ACCS | audits selected action claims | not a new feasible-action learner |

### Upgraded working title

首选题目：

> **Calibration After Action Selection: Safety Claims for Offline RL under Moving Budgets**

更稳的 AAAI 题目：

> **A Cost Constraint Is Not a Certificate: Calibration After Action Selection in Offline RL**

原题 `When Constraints Move` 可以作为 subtitle 或 intro hook，但不再是最强 headline。

### Upgraded Figure 1

旧 Figure 1 只是展示：

```text
fixed-budget policy violates stricter unseen budgets
```

升级后的 Figure 1 必须更尖锐：

```text
Two methods can both satisfy aggregate episode cost,
while one relies on actions that have no calibrated support
under the deployment constraint.
```

这张图要让 reviewer 立刻看到：aggregate cost success 与 deployable action claim support 是两件事。

### New evaluation object: selected-claim false certification

新增核心指标：

```text
False certification among issued claims =
P[residual cost exceeds budget | certificate issued after action selection]
```

可操作指标：

| Metric | Meaning |
|---|---|
| False Certification Rate | failure rate among issued/selected action claims |
| Claim Yield | fraction of a fixed proposal stream receiving a certificate |
| Risk-Coverage Curve | utility/yield as the target false-certification risk changes |
| Utility at Controlled Risk | task return while selected-claim risk is controlled |
| Fallback Cost | reward/cost incurred when certification abstains |
| Worst-Group False Certification | subgroup failure among issued claims |

如果实验只证明 ACCS reward/cost 更好，论文还是 incremental。若实验证明普通 conformal / learned feasibility score 在 action selection 后 false certification 飙升，而 selection-aware ACCS 能把 issued-claim risk 拉回目标水平并保留足够 utility，论文才有 oral 味道。

## 0B. 从三个参考项目迁移过来的论文形态

`ICLR_1` 给本项目的最重要经验不是 IVS 这个具体工具，而是论文结构：

1. 先攻击一个领域默认假设。
2. 把一个被混成单一指标的东西拆成多个证据轴。
3. 用一张反直觉主现象表让 reviewer 记住问题。
4. 方法是服务于证据轴的诊断/控制协议，而不是堆模块。
5. 理论只承诺自己能承诺的边界。
6. 每个实验只服务一个 claim。
7. 最后用 claim-evidence map 和 adversarial review 收口。

`AAAI_1` 给本项目的经验是：learned 系统不能自己决定 claim 的含义。模型可以提出候选，但 verifier/calibrator 决定哪些 claim 能被接受。

`ICLR_2` 给本项目的经验是：不要把 headline 成功率当最终证据。失败、fallback、abstention、budget sensitivity 都应成为可审计信号。

因此 `AAAI_2` 的主线应从：

```text
Action-conditional conformal shield for offline safe RL
```

升级为：

```text
Moving constraints expose a missing action-safety evidence axis:
fixed-budget safe RL performance is not a deployable safety claim.
```

---

## 1. 最终一句话

Offline safe RL 通常在一个固定训练约束下学习并评测 policy，但部署时安全预算、法规阈值、用户偏好和环境风险会变化。本文主张：

> **Safety is not a scalar cost attached to a policy. It is a deployment-time claim about an action under a requested constraint, and that claim must carry calibration evidence or be refused.**

推荐英文题目：

> **Calibration After Action Selection: Safety Claims for Offline RL under Moving Budgets**

备用题目：

> **A Cost Constraint Is Not a Certificate: Calibration After Action Selection in Offline RL**

系统名：

> **ACCS**：Action-Selection-Aware Conformal Certification / Action-Conditional Conformal Selection

中文标题：

> **动作选择后的安全校准**

---

## 2. 论文灵魂

### 2.1 反直觉主张

领域默认：

> offline safe RL policy 在测试时满足给定 cost budget，就说明它是安全的。

本文攻击这个默认：

> Fixed-budget safety is not deployment safety. A policy can look safe under the training/evaluation budget, but become uncertified or overly conservative when the constraint moves.

更强的说法：

> Safety is not a scalar property of a policy. It is a calibrated, budget-conditioned, action-level claim.

这个主张的反直觉性来自三点：

1. **reward-cost Pareto 好看不等于可部署。** 同一 policy 在新 budget 下可能没有任何 action-level certificate。
2. **全局 conformal safety 可能控制 violation，但会把安全动作也误杀。** 这不是安全胜利，而是 utility collapse。
3. **action-level coverage 不自动推出 horizon-level safety。** 序列决策带来的分布漂移必须单独审计。

### 2.2 论文口径

不要说：

> We add conformal prediction to offline safe RL.

要说：

> We introduce a calibrate-or-abstain action-safety protocol for offline policies under evolving deployment constraints. A proposed action is executed only if a held-out, action-conditional conformal certificate supports its cost claim under the current budget.

### 2.3 和 `ICLR_1` 的同构关系

| `ICLR_1` | `AAAI_2` |
|---|---|
| restoration 不等于机制证据 | fixed-budget return 不等于部署安全证据 |
| `R/V/A` 三轴 | `U/C/A/H` 四轴 |
| IVS 是 conditional validity diagnostic | ACCS 是 conditional action-safety certificate |
| high restoration + low validity 是危险区 | high reward + low calibration / unseen budget 是危险区 |
| repair 不等于机制对齐 | shielding 不等于 horizon guarantee |

---

## 3. 证据轴：U/C/A/H

本文稳定使用四个证据轴，不再只报告 reward 和 total cost。

| 轴 | 名称 | 审稿人问题 | 指标 |
|---|---|---|---|
| `U` | Utility retention | policy 还保留多少任务收益？ | normalized return, reward loss, Pareto frontier |
| `C` | Calibration | action cost upper bound 是否覆盖真实 future cost？ | empirical coverage, calibration error, group-wise coverage |
| `A` | Adaptivity | 不重训时能否适配 unseen budgets？ | verified coverage across budgets, adaptation latency, abstention rate |
| `H` | Horizon risk | 序列 rollout 下 violation 是否仍受控？ | episode violation rate, cumulative cost exceedance, risk allocation audit |

核心层级：

```text
U does not imply C.
C at one budget does not imply A across budgets.
Action-level C does not imply horizon-level H.
H must be empirically audited under induced policy shift.
```

这就是论文的理论和实验骨架。所有摘要和引言 claim 都必须能挂到这四轴之一。

---

## 4. 主问题定义

### 4.1 Offline policy and moving deployment budget

给定离线数据：

```text
D = {(s_t, a_t, r_t, c_t, s_{t+1})}
```

其中 `c_t` 是 safety cost。已有 offline RL 或 offline safe RL 方法先训练一个基础 policy：

```text
pi_0(a | s)
```

训练时可能使用固定 budget `b_train`，但部署时 budget 变成：

```text
b_deploy in B = {stricter, looser, user-specific, region-specific, time-varying}
```

例子：

- robot navigation: collision budget 从 10 降到 5。
- autonomous driving: lane violation budget 因地区法规改变。
- healthcare/resource control: energy or intervention cost budget 因用户偏好改变。
- content moderation or recommendation: toxic/action-risk tolerance 改变。

### 4.2 Action-safety random variable

定义某个状态动作对的未来安全成本：

```text
Z_H(s, a; pi_exec) = sum_{t=0}^{H-1} c_t
```

其中第一步执行 action `a`，之后由执行 policy `pi_exec` 或 fallback controller 接管。`Z_H` 可以是 finite horizon cost、discounted cost、或 episode residual cost。

目标不是直接证明 `pi_0` 全局安全，而是对每个候选动作产生一个可审计声明：

```text
Claim(s, a, b, alpha):  Z_H(s,a) <= b  with miscoverage <= alpha
```

升级后这个 claim 必须显式带 provenance：

```text
Claim(s, a, b, alpha, provenance)
```

其中 `provenance` 至少包含：

```text
state/action group
calibration sample size
cost estimate
conformal radius
upper cost certificate
requested budget
alpha level
fallback or abstention reason
```

这条 provenance 是和现有 policy-learning 方法拉开距离的关键。没有 provenance 的 aggregate safety 只能说明 episode cost 低，不能说明部署时每个 action 的 safety claim 已经被证据支持。

### 4.3 Shield decision

ACCS 构造一个部署时安全动作集合：

```text
A_cert(s, b, alpha) = {a in A : U_c(s,a,alpha) <= b}
```

执行规则：

```text
if a_0 ~ pi_0(.|s) is in A_cert:
    execute a_0
elif A_cert is nonempty:
    execute argmax_{a in A_cert} Q_r(s,a)
else:
    abstain / fallback / hand over to conservative controller
```

关键点：`abstain` 不是失败，而是防止无证据 action 被伪装成安全 action。

### 4.4 Budget-uniform certificate surface

最强理论对象不是 budget-conditioned policy，而是 budget-independent certificate surface：

```text
U_c(s,a,alpha)
```

部署时任意 budget 只做后验阈值查询：

```text
A_cert(s,b,alpha) = {a : U_c(s,a,alpha) <= b}
```

这段现在只保留为实现接口，不作为主要理论贡献。真正的理论贡献必须处理：

```text
selection can concentrate calibration failures among issued action claims.
```

---

## 5. 主现象：Marginal Calibration Can Fail After Action Selection

这篇需要一张像 `ICLR_1` Table 1 那样的主表。建议第一批 toy/Safety-Gym 结果就按下面形状设计。

| Method | Proposal coverage | Issued false cert. | Claim yield | Reward | Verdict |
|---|---:|---:|---:|---:|---|
| uncalibrated score | poor | high | high | high | unsafe thresholding |
| global CP | nominal | high after selection | high | high | marginally valid but selected-risk fails |
| group CP | nominal by group | still high if selection concentrates errors | medium | medium | grouping helps but is not enough |
| conformal risk control | target-dependent | lower | medium | medium | strong baseline |
| selective/FCR baseline | controls issued risk | medium/low | medium | medium | statistical baseline |
| **selection-aware ACCS** | nominal | near target | useful | high-medium | target method |

这张表要支撑的结论：

> Marginal calibration over candidate actions does not imply calibrated claims for the actions selected and executed.

---

## 6. 方法：ACCS as Selection-Aware Auditing

### 6.1 Pipeline overview

ACCS 有五个模块：

```text
proposal stream + declared continuation policy
  -> cost / feasibility score
  -> marginal calibration primitive
  -> selection-aware risk control / FCR correction
  -> issue certificate or abstain/fallback
  -> rollout and horizon audit
```

方法部分必须按“模块动机 -> 设计 -> 技术优势”写，而不是只列公式。

### 6.2 Cost-return model

训练一个 cost return predictor：

```text
Q_c_hat(s, a) ≈ E[Z_H(s,a)]
```

推荐实现：

- ensemble critics for epistemic uncertainty；
- quantile or distributional cost critic；
- reward critic `Q_r` 与 cost critic 分开，避免 reward objective 污染 safety calibration；
- calibration split 与 training split 严格分开。

输出：

```text
mu_c(s,a), sigma_c(s,a), optional quantile estimate
```

基础 nonconformity score：

```text
e_i = Z_i - Q_c_hat(s_i, a_i)
```

可选 normalized score：

```text
e_i = (Z_i - Q_c_hat(s_i,a_i)) / (sigma_c(s_i,a_i) + eps)
```

### 6.3 Action-conditional calibration

全局 conformal threshold：

```text
q_global = Quantile_{1-alpha}({e_i})
```

会被高风险动作拖得过保守。ACCS 改为 action-conditioned groups：

```text
g = G(s,a)
q_g = Quantile_{ceil((n_g+1)(1-alpha))/n_g}({e_i : G(s_i,a_i)=g})
U_c(s,a) = Q_c_hat(s,a) + q_g
```

`G(s,a)` 可以来自：

1. discrete action bucket；
2. continuous action clustering；
3. risk embedding cluster；
4. state-action nearest-neighbor cell；
5. learned latent cluster，但 clustering 必须在 calibration 之外固定。

**写作重点**：action conditioning 不是为了让公式更复杂，而是为了避免把不同风险机制混成一个 threshold。它对应 `ICLR_1` 的 conditional validity：reference distribution 必须和 claim 对象一致。

### 6.4 Hierarchical calibrate-or-abstain

action group 的样本数不足时不能假装有证据。采用层级 fallback：

```text
specific action group
  -> coarser risk group
  -> global threshold
  -> abstain
```

规则：

```text
if n_g >= n_min:
    use q_g
elif n_parent >= n_min:
    use q_parent
elif global_allowed:
    use q_global
else:
    abstain
```

每个 issued claim 输出一条 action-safety report：

```json
{
  "state_id": "...",
  "action": "...",
  "budget": 5.0,
  "alpha": 0.05,
  "group": "turn-left/high-speed",
  "calibration_n": 143,
  "cost_pred": 3.1,
  "conformal_radius": 1.2,
  "upper_bound": 4.3,
  "decision": "accept"
}
```

这借鉴 `AAAI_1` 的 verifier-owned claim contract：模型给 prediction，auditor 决定 claim 是否能被发行。

### 6.5 Constraint-adaptive shield

部署时只改变 `b`，不重训 `pi_0` 和 critic：

```text
A_cert(s,b,alpha) = {a : U_c(s,a,alpha) <= b}
```

性质：

```text
if b1 <= b2, then A_cert(s,b1,alpha) subseteq A_cert(s,b2,alpha)
```

这给 unseen budget adaptation 一个干净的实验接口：同一批 calibrated upper bounds 可以在多个 budget 下重筛 action。

执行策略：

```text
a_0 = sample_or_argmax pi_0(.|s)
if certified(a_0):
    execute a_0
else:
    execute argmax_{a in A_cert} Q_r(s,a)
if A_cert empty:
    fallback / abstain
```

可选增强：

- budget residual `b_t = b - accumulated_cost`；
- action replacement penalty；
- fallback controller；
- policy library switching，但必须作为 baseline/extension，不要让它抢主线。

### 6.6 Sequential risk monitor

RL 的 sequential shift 是最大理论风险。主文必须诚实：

```text
action-level calibration != full trajectory safety guarantee
```

可做两层处理：

1. **Risk allocation**：每步使用 `alpha_t`，满足 `sum_t alpha_t <= alpha_episode`。
2. **Empirical horizon audit**：报告 episode violation、cumulative cost exceedance、coverage degradation by time。

可选在线增强：

- weighted conformal prediction；
- importance-weighted calibration；
- rolling recalibration buffer；
- martingale coverage monitor；
- shift detector triggering abstention。

这些是增强，不是核心 theorem。

---

## 7. 理论路线

理论目标：像 `ICLR_1` 和 `AAAI_1` 一样，每个命题包含 claim、statement、proof sketch、empirical prediction、evidence status。

### Proposition 1: Action-Conditional Coverage

**Claim**  
在固定 action group 内，如果 calibration examples 与 deployment queried action 满足 group-conditional exchangeability，则 ACCS 的 upper bound 有 finite-sample coverage。

**Statement**

For group `g`, let calibration scores be:

```text
E_g = {Z_i - Q_c_hat(s_i,a_i) : G(s_i,a_i)=g}
```

Let `q_g` be the conformal quantile. For a new `(s,a)` with `G(s,a)=g`:

```text
P[Z_H(s,a) <= Q_c_hat(s,a) + q_g | G(s,a)=g] >= 1 - alpha
```

**Empirical prediction**

Group-wise empirical coverage should be near or above `1-alpha`, while global conformal may over-cover low-risk groups and under-diagnose high-risk groups.

### Proposition 2: Selection Can Concentrate Calibration Failures

**Claim**  
普通 conformal upper bound 可以在所有 proposals 上 marginally valid，但经过部署时 action selection 后，false certification 会集中到真正执行/发行 claim 的动作上。

**Forbidden old inference**

```text
P[Z <= U] >= 1-alpha  and  accept if U <= b
does not imply
P[Z > b | accept] <= alpha
```

只能推出：

```text
P[Z > b | accept] <= alpha / P[accept]
```

**Empirical prediction**

Phase 1 exact toy 必须显示：global/group conformal 在 proposal distribution 上 coverage nominal，但选择 highest-reward certified action 后，issued-claim false certification 大幅超过 alpha；selection-aware ACCS 或 selective/FCR baseline 才能修复。

### Proposition 3: Policy-Specific Residual-Cost Target

**Claim**  
Residual-cost certificate 必须声明 continuation policy。普通 offline trajectory 下的 `Z_H^beta` 不等于部署执行 policy 下的 `Z_H^{pi_cont}`。

**Statement**

```text
Z_H^{beta}(s,a) != Z_H^{pi_cont}(s,a)
```

除非 calibration labels 来自 exact continuation policy、有效 off-policy conformal/OPE、可靠 model-based target，或目标降级为 one-step cost。

**Empirical prediction**

Phase 1/2 必须使用 simulator branching 或 exact toy ground truth 验证 policy-specific residual risk。

### Proposition 4: No-Overlap Impossibility

**Claim**  
如果 deployment query 落在 calibration distribution 无 support 的 state-action region，任何 distribution-free certifier 都不能发行 nontrivial valid safety claim；必须 abstain/fallback。

**Empirical prediction**

support stress test 中 claim yield 应下降、abstention 上升；若方法继续发行 claim，false certification 会升高。

### Proposition 5: Selection-Aware False Certification Control

**Claim target**  
真正需要证明的是 issued claims 上的 false certification，而不是所有 proposals 上的 marginal coverage。

**Target statement**

```text
P[Z_H^{pi_cont}(s,a) > b | certificate issued, group g, budget b] <= alpha
```

或 FCR 形式：

```text
E[# false issued claims / max(1, # issued claims)] <= alpha
```

under declared proposal distribution, selection rule, budget query rule, continuation policy, and support assumptions.

### Proposition 6: Budget Monotonicity

**Claim**  
同一个 calibrated upper bound 可以支持多个 deployment budgets，且安全动作集合随 budget 单调扩张。

**Statement**

If `b1 <= b2`, then:

```text
A_cert(s,b1,alpha) subseteq A_cert(s,b2,alpha)
```

**Empirical prediction**

reward-cost frontier 应随 budget 平滑变化；adaptation latency 近似为 action filtering cost，而非 retraining cost。

### Proposition 7: Calibration Granularity Tradeoff

**Claim**  
更细的 action groups 降低过保守性，但增加样本不足与 abstention 风险。

**Statement**

Fine groups reduce within-group score variance but increase quantile variance and empty-group probability. Therefore ACCS needs hierarchical fallback and must report abstention.

**Empirical prediction**

group granularity sweep 应出现 Pareto：safe set size/reward improves up to a point, then coverage noise or abstention increases。

### Proposition 8: Horizon-Level Boundary

**Claim**  
Action-level conformal coverage alone does not solve policy-induced sequential distribution shift。

**Statement**

If each step's queried state-action pair satisfies the relevant exchangeability condition and `sum_t alpha_t <= alpha`, then union bound gives:

```text
P[any step action-cost certificate fails] <= alpha
```

But if shield-induced policy shift changes the state distribution outside calibration support, this condition can fail.

**Empirical prediction**

distribution shift experiments should show where group coverage degrades; online recalibration or weighted conformal should mitigate but not magically eliminate the issue。

### Supporting Observation A: Aggregate Safety Cannot Identify Claim Support

**Claim**  
仅报告固定 budget 下的 aggregate reward/cost，无法判断一个 policy 的 action-level safety claims 是否可发行。

**Statement**

Construct two policies or MDP instances with identical aggregate cost distribution under the reported evaluation budget but different residual action-cost distributions for deployment queries. Any evaluator that observes only aggregate fixed-budget cost cannot distinguish whether the deployment actions have calibrated claim support.

**Empirical prediction**

Toy construction should show two methods with similar episode cost but sharply different selected-claim false certification and claim yield.

### Supporting Observation B: Global Marginal Calibration Is Not Enough After Selection

**Claim**  
全局 conformal threshold 可以 marginally valid，但可能在 selected claims 上失效或非常低效。

**Statement**

If action groups and reward scores have heterogeneous residual-cost distributions, a global threshold can be valid before selection but inefficient or unsafe after selection. The paper should compare global CP, group CP, conformal risk control, and selection-aware ACCS.

**Empirical prediction**

Global conformal may look nominal over proposals while showing high false certification or poor utility/yield among issued claims.

---

## 8. 实验矩阵

### E0: Exact Selection-Failure Toy

目的：先在 exact finite MDP 中证明普通 conformal calibration 在 action selection 后会失效；如果这个现象打不穿，不要跑 Safety-Gym / DSRL。

环境：

- finite tabular MDP or one-state K-action construction；
- exact residual-cost distribution known by enumeration / simulator branching；
- candidate action set size `K in {2,4,8,16}`；
- learned cost score with calibrated marginal residuals；
- reward score correlated with calibration error；
- fixed budget grid and declared continuation policy。

必须画：

1. marginal coverage over all proposals is nominal；
2. selected/issued-claim false certification is much higher than alpha；
3. false certification increases with candidate set size `K`；
4. global CP vs group CP vs conformal risk control vs selective/FCR baseline vs selection-aware ACCS；
5. support stress: unsupported regions trigger abstention/fallback；
6. utility at controlled false-certification risk。

主张：

> marginal calibration before selection does not imply calibrated safety claims after deployment-time action selection.

### E1: Policy-Specific Residual-Cost Validation

目的：确认 `Z_H^{pi_cont}(s,a)` 的 label 确实对应声明的 continuation policy。

必须做：

1. declare proposal policy, selection rule, continuation policy, fallback, horizon；
2. simulator branching from sampled state-action queries；
3. many continuations per query to estimate true residual-budget violation；
4. compare behavior-policy residual labels vs deployment-continuation residual labels；
5. decide whether main experiments can use simulator branching, off-policy conformal/OPE, model-based target, or one-step target。

### E2: Main Unseen-Budget Evaluation

主 benchmark：

1. Safety-Gymnasium Point / Car tasks；
2. DSRL offline safe datasets；
3. 如果已有 pipeline，再加 MetaDrive driving case study。

设置：

```text
train/calibrate on budgets: {10, 20}
test on budgets: {3, 5, 8, 12, 15, 25}
```

指标：

- normalized return；
- total cost；
- budget violation rate；
- utility at controlled false-certification risk；
- claim yield；
- false certification among issued claims；
- risk-coverage curve；
- certified action coverage；
- abstention/fallback rate；
- action replacement rate；
- adaptation latency；
- group-wise empirical coverage。

主张：

> selection-aware ACCS maintains issued-claim false-certification control across moving budget queries while retaining useful reward/yield.

### E3: Selection-Aware vs Marginal Conformal

比较：

- global split conformal；
- group/Mondrian conformal；
- conformal risk control；
- CAP/selective conformal baseline；
- selection-aware ACCS；
- uncalibrated learned score。

关键图：

```text
x-axis: false certification among issued claims
y-axis: claim yield / reward
```

主张：

> the contribution is selection-aware false-certification control, not merely finer action grouping.

### E4: Calibration Diagnostics

按 group 报告：

- `n_calib`；
- conformal radius；
- empirical coverage；
- mean cost；
- issued claim fraction；
- reward loss。

必须展示：

1. high-risk actions 的 quantile 更大；
2. low-risk actions 不应被 global threshold 过度惩罚；
3. sample-poor groups 触发 fallback/abstain。

主张：

> ACCS is not just a better aggregate metric; it gives auditable action-safety reports.

### E5: Distribution Shift Stress Test

改变：

- obstacle density；
- friction / dynamics；
- cost noise；
- dataset quality: expert / medium / random / mixed；
- behavior policy mismatch；
- unseen action region。

比较：

- vanilla ACCS；
- weighted ACCS；
- online recalibration；
- shift-triggered abstention。

主张：

> sequential/distribution shift is a real boundary; ACCS can diagnose and partially mitigate it, but should not overclaim full guarantee.

### E6: Calibrate-or-Abstain Boundary

专门测试 evidence insufficiency：

- rare action groups；
- continuous action clusters with sparse calibration；
- new user budget too strict；
- state-action OOD detector flags low support。

指标：

- abstention reason breakdown；
- fallback safety；
- utility cost of abstention；
- violation avoided by abstention。

主张：

> abstention is necessary claim discipline, not a cosmetic add-on.

### E7: Sequential Risk Allocation

设置：

- fixed `alpha_episode`；
- compare uniform `alpha_t` vs cost-aware `alpha_t`；
- horizon lengths `{25, 50, 100}`。

指标：

- per-step coverage；
- episode violation；
- cumulative cost exceedance；
- union-bound conservatism；
- empirical calibration drift over time。

主张：

> action-level guarantees can be composed conservatively, but the horizon-level story must be audited empirically.

### E8: Safety-Critical Case Study

推荐 driving / lane violation：

```text
policy is aggressive under normal budget
deployment budget suddenly tightens
ACCS filters lane-risk actions and shifts to conservative alternatives
```

图：

- trajectory visualization；
- selected action groups over time；
- budget residual；
- shield interventions。

### E9: Ablations

| Variant | 去掉什么 | 预期 |
|---|---|---|
| no calibration | only critic threshold | coverage unreliable |
| global conformal | no action conditioning | over-conservative |
| no hierarchy | no fallback | sparse groups fail |
| no abstain | force action | high violations in sparse/OOD groups |
| no ensemble/uncertainty | raw mean cost | weaker calibration under shift |
| no residual budget | static budget only | worse horizon violation |
| online recalibration only | no action grouping | adapts but may be noisy |

---

## 9. Baselines

必须包含：

| Baseline | 作用 |
|---|---|
| uncalibrated learned score | 证明 score thresholding 会产生 false certification |
| global split conformal | 证明 marginal coverage 不等于 selected-claim control |
| group/Mondrian conformal | 区分 grouping vs selection correction |
| conformal risk control | 风险控制强 baseline |
| CAP/selective conformal baseline | post-selection/FCR 强 baseline |
| selection-aware ACCS | 目标方法 |
| **CAPS** | 直接竞争者；action filtering / policy switching prior |
| CAPS + global CP | 区分 CAPS 与普通 conformal wrapping |
| CAPS + group CP | 区分 grouping 与 selection-aware correction |
| **CAPS + selection-aware ACCS** | 证明强 constraint-adaptive policy 仍需要 auditing layer |
| **SafeFQL** | conformal offline safe RL 直接威胁 |
| policy switching / conservative fallback | 对比 retrain-free adaptation |
| CQL-Lagrangian / BCQ-Lagrangian / CPQ / COptiDICE 类 offline safe RL | 对齐领域基线 |
| retrain-per-budget policy | expensive upper bound，不一定主 baseline |
| oracle cost model shield | upper bound / diagnostic only |

公平性要求：

- 同一 offline dataset；
- 同一 evaluation budgets；
- 同一 rollout seeds；
- 同一 fallback budget accounting；
- calibration split 不得泄漏到 training。

---

## 10. 图表规划

### Figure 1: Main Phenomenon

标题：

> Aggregate safety can hide unsupported deployment actions.
> Marginal calibration can fail after action selection.

内容：

- global/group conformal 在 proposals 上 nominal；
- 选择最高 reward 的 certified action 后 false certification 飙升；
- failure 随 candidate-set size `K` 增大；
- selection-aware ACCS / selective baseline 控制 issued-claim false certification；
- abstention 在 unsupported regions 上升。

### Figure 2: ACCS Pipeline

```text
offline data -> cost critic -> action groups -> conformal upper bounds
             -> budget filter -> execute / replace / abstain
```

### Figure 3: Risk-Coverage Frontier

`false certification among issued claims` vs `claim yield / reward`。

### Figure 4: Group-Wise Calibration Heatmap

每个 action group 的：

- conformal radius；
- empirical coverage；
- accepted fraction。

### Table 1: Selection-Failure Main Table

主现象表：uncalibrated score / global CP / group CP / CRC / selective CP / selection-aware ACCS。

### Table 2: Main Benchmark Results

多环境、多 budget、多 seed。

### Table 3: Ablation

覆盖 action conditioning、hierarchy、abstain、uncertainty、online recalibration。

### Figure 5: Horizon Risk Audit

per-step coverage 和 episode violation 随 horizon 的变化。

---

## 11. 论文结构

推荐 7 页 AAAI 主文结构：

1. **Introduction**
   - aggregate reward/cost evaluation 的部署缺口；
   - learned feasibility score 与 calibrated deployment certificate 的区别；
   - calibration after action selection；
   - `U/C/A/H` 证据轴；
   - ACCS 的 selection-aware audit protocol；
   - 主现象和贡献。

2. **Problem Formulation**
   - offline policy；
   - moving budgets；
   - action-safety claim；
   - execute / replace / abstain。

3. **Method: ACCS**
   - cost-return model；
   - proposal stream and continuation policy；
   - marginal calibration primitive；
   - selection-aware false-certification control；
   - fallback and abstention；
   - sequential risk monitor。

4. **Theory**
   - action-conditional coverage；
   - budget violation corollary；
   - budget monotonicity；
   - fixed-budget aggregate evidence insufficiency；
   - global calibration limitation；
   - horizon-level boundary。

5. **Experiments**
   - exact selection-failure toy；
   - policy-specific residual-cost validation；
   - risk-coverage frontier；
   - CAPS/SafeFQL comparisons after toy success。

6. **Diagnostics and Ablations**
   - group-wise calibration；
   - distribution shift；
   - abstention boundary；
   - horizon audit。

7. **Discussion and Limitations**
   - exchangeability；
   - sequential shift；
   - sparse calibration groups；
   - when to abstain or recalibrate。

---

## 12. 摘要骨架

```text
Offline safe reinforcement learning methods often select deployment actions by thresholding learned cost or feasibility scores. Even when these scores admit marginal conformal calibration over candidate proposals, deployment-time action selection can concentrate calibration errors among the actions that are actually certified and executed. We study this calibration-after-selection problem for offline safe RL under moving budget queries. The intended contribution is not another constraint-adaptive policy optimizer, but a selection-aware auditor that targets false certification among issued action claims for a declared proposal stream, continuation policy, and support condition. The first required evidence is an exact counterexample showing that ordinary global or group conformal calibration can remain nominal over proposals while failing after action selection.
```

---

## 13. Introduction 结构草案

1. **Opening**
   - offline safe RL matters in robotics/driving/resource allocation；
   - but evaluation often reports aggregate reward/cost under one or a few budgets。

2. **Failure of default assumption**
   - deployment budgets move；
   - learned feasibility scores are not calibrated deployment certificates；
   - action selection can concentrate calibration failures。

3. **Evidence-axis split**
   - introduce `U/C/A/H`；
   - add false certification among issued claims and claim yield。

4. **Method**
   - ACCS as selection-aware auditor；
   - declared proposal stream / continuation policy / fallback；
   - false-certification control or diagnosis among issued claims。

5. **Evidence**
   - main phenomenon table；
   - unseen-budget benchmarks；
   - diagnostics and limitations。

6. **Contributions**
   - formulation；
   - method；
   - theorem；
   - experiments；
   - reporting checklist。

---

## 14. 工程执行路线

### Phase 0: Protocol freeze

- 固定 offline dataset split：train / calibration / test。
- 固定 action group construction，不许用 test 调。
- 定义 action-safety report JSON。
- 写 `experiment_report.md` 和 `claim_evidence_map.md`。

### Phase 1: Exact selection-failure toy

目标：一周内出 Figure 1 / Table 1 雏形。

- finite MDP or one-state K-action construction；
- exact residual-cost distribution under declared continuation policy；
- global CP / group CP nominal over proposals；
- selected-action false certification after highest-reward certified action；
- uncalibrated score / global CP / group CP / conformal risk control / selective baseline / selection-aware ACCS；
- claim yield, false certification, risk-coverage, reward, fallback。

Go 标准：

- global/group CP over proposals has nominal coverage；
- selected-action false certification 明显超过 alpha；
- failure 随 candidate-set size `K` 增大；
- selection-aware ACCS 或 selective/FCR baseline 修复 false certification；
- in-support claim yield 不塌。

### Phase 2: ACCS prototype

- cost-return ensemble；
- proposal stream interface；
- declared continuation policy and fallback interface；
- global CP / group CP / CRC / selective-FCR baselines；
- selection-aware false-certification control；
- support diagnostics and abstention；
- issued-claim report logging。

### Phase 3: Safety-Gymnasium main

- only after Phase 1/2 pass；
- 2-3 个环境；
- 5 个 budgets；
- 5 seeds；
- baselines：global CP/group CP/CRC/selective baseline/CAPS/SafeFQL if feasible。

### Phase 4: DSRL and stronger baselines

- 接 DSRL；
- CQL-Lagrangian/CPQ/COptiDICE 类 baseline；
- CAPS / CAPS+global CP / CAPS+group CP / CAPS+selection-aware ACCS；
- SafeFQL；
- retrain-per-budget optional upper bound。

### Phase 5: Distribution shift and horizon audit

- dynamics/cost/noise/data quality shift；
- weighted conformal / online recalibration；
- risk allocation。

### Phase 6: Writing and adversarial review

- theorem section；
- main figures/tables；
- claim-evidence map；
- limitation language；
- 7-page compression。

---

## 15. Claim-Evidence Map

| Claim | Required evidence | Status |
|---|---|---|
| Learned feasibility scores are not calibrated deployment certificates. | Exact toy showing nominal proposal coverage but selected-claim failure. | pending |
| Marginal conformal does not control issued-claim risk after selection. | Global/group CP accepted-set counterexample. | pending |
| ACCS targets false certification among issued claims. | Selection-aware theorem or CRC/FCR-style guarantee + toy evidence. | pending |
| Residual-cost certificates are policy-specific. | Formal `Z_H^{pi_cont}` + simulator branching / exact labels. | pending |
| No support implies abstention is necessary. | No-overlap theorem + support stress test. | pending |
| Strong constraint-adaptive methods still need finite-data auditing. | CAPS vs CAPS+global/group/selective ACCS comparison. | pending |
| SafeFQL is prior work but not the full selection-aware moving-budget story. | Full SafeFQL comparison or precise limitation. | pending |
| Horizon-level safety is a separate empirical boundary. | Risk allocation theorem + episode violation audit under shift. | pending |
| Distribution shift can degrade coverage but is diagnosable. | shift experiments with false certification and support diagnostics. | pending |

---

## 16. Reviewer 风险与预防

| 质疑 | 预防 |
|---|---|
| 这只是 conformal prediction + safe RL。 | 主线写成 calibration after action selection；普通 conformal 是会失败的 baseline。 |
| SafeFQL 已经做了。 | 承认 SafeFQL；只 claim selection-aware false certification under candidate/budget queries。 |
| accepted-action theorem 错。 | 删除旧 Proposition 2；只证明/实验 false certification among issued claims。 |
| residual-cost target 不可观测。 | 显式定义 `Z_H^{pi_cont}`；先做 exact toy / simulator branching。 |
| action-level guarantee 对 RL horizon 没用。 | 明确理论边界；horizon-level 用 risk allocation + empirical audit，不夸大。 |
| action groups 是拍脑袋。 | group granularity sweep + state/action/global baselines + sample-size fallback。 |
| coverage 假设不成立。 | 把 exchangeability 写清楚；做 distribution shift stress 和 weighted/online variants。 |
| reward 下降太多。 | 报 risk-coverage frontier、claim yield、fallback cost、global/group/selective baselines。 |
| abstention 让任务不可用。 | 报 abstention reason、fallback performance、utility cost，并把它定位为 claim discipline。 |
| baseline 不够强。 | 加 offline safe RL baselines、policy switching、pessimism、global/state conformal、retrain upper bound。 |
| calibration/test 泄漏。 | protocol freeze；train/calibration/test split；所有 group 规则在 calibration 前固定。 |

---

## 17. 最小强版本

如果时间紧，最小可投稿版本：

1. moving-budget problem formulation；
2. `U/C/A/H` evidence hierarchy；
3. ACCS action-conditional conformal shield；
4. finite-sample action-level theorem；
5. toy main phenomenon；
6. Safety-Gymnasium 2-3 环境；
7. no shield / global conformal / state-only / pessimism baselines；
8. group-wise coverage diagnostics；
9. abstention boundary；
10. clear limitation on horizon-level guarantee。

不要在最小版本里铺太宽：

- 不要主打 MetaDrive；
- 不要承诺 full safe RL theory；
- 不要把 online recalibration 写成主方法；
- 不要把 retrain-per-budget 当必须跑满的大实验。

---

## 18. Oral 潜力版本

额外增强：

1. DSRL full benchmark；
2. MetaDrive case study；
3. learned risk embeddings for action grouping；
4. weighted conformal under distribution shift；
5. online coverage martingale monitor；
6. policy-library fallback；
7. open-source action-safety report suite；
8. formal treatment of nested budgets and simultaneous budget queries。

---

## 19. 写作红线

稳定使用：

- moving deployment constraints；
- action-safety claim；
- calibrate-or-abstain；
- action-conditional conformal shield；
- group-wise coverage；
- retrain-free adaptation；
- risk-coverage frontier；
- horizon-level empirical audit。

避免：

- “guarantees safe RL”；
- “solves sequential distribution shift”；
- “always controls episode-level violation”；
- “conformal shield is distribution-free under policy shift”；
- “no retraining means no cost”；
- “abstention is failure”；
- “global conformal is bad” without matched-risk evidence。

---

## 20. 最终判断

这条线可以做，但必须像 `ICLR_1` 那样把灵魂放在前面：

> **When constraints move, policy-level safety claims break. ACCS turns safety into an action-level, calibrated, budget-conditioned claim, and refuses to execute actions when the evidence is insufficient.**

如果只写成“action-conditional conformal prediction for offline safe RL”，新颖性会显得自然、增量、容易被打成组合。  
如果写成“fixed-budget safe RL evaluation conflates utility, calibration, adaptivity, and horizon risk”，并用 moving-budget 主现象表、group-wise coverage、abstention boundary 和清晰理论边界支撑，论文形态就更接近 `ICLR_1` 的成功模板。

---

## 21. 项目生产流程

本项目按 `ICLR_1` / `AAAI_1` / `ICLR_2` 的生产方式推进：

```text
local Windows = 写代码、读论文、分析结果、写论文、做 smoke test
servers       = 正式实验、多 seed、benchmark、主表主图
reports       = 所有 claim 的唯一证据账本
```

### 21.1 本地职责

本地根目录：

```text
D:\AAAI_2
```

本地只做：

1. 代码开发和小规模 smoke test；
2. 实验脚本、分析脚本、绘图脚本；
3. 论文写作和 claim-evidence 审计；
4. 服务器输出下载后的表格整理；
5. 文档维护。

本地结果默认不能进入论文主表。若使用本地结果，只能标注为 `local smoke test`。

### 21.2 服务器职责

正式实验必须在 4090 或 A40 服务器运行，并输出到：

```text
outputs/*_server.json
outputs/*_server.md
```

正式论文数字只从以下来源进入：

1. `outputs/*_server.json`
2. `outputs/*_server.md`
3. `analysis/paper_assets/*`
4. 明确记录在 `experiment_report.md` 的 canonical outputs

### 21.3 文件职责

| 文件 | 职责 |
|---|---|
| `idea_blueprint.md` | 论文大方向、主线、实验矩阵 |
| `EXPERIMENT_MANUAL.md` | 服务器、本地环境、同步命令、运行规范 |
| `EXPERIMENT_FIX_PLAN.md` | 实验失败后的修正路线和风险预案 |
| `NEXT_STEPS.md` | 只记录未完成的下一步 |
| `experiment_report.md` | 已完成实验、证据账本、正式结论 |
| `theory_proofs.md` | 定义、命题、证明草图、理论-实验映射 |
| `analysis/claim_evidence_map.md` | 摘要/引言每个 claim 对应证据 |
| `analysis/adversarial_review.md` | 站在 reviewer 角度的拒稿风险审计 |
| `analysis/reproduction_log.md` | 服务器命令、paper compile、artifact 变更记录 |
| `src/README.md` | 代码架构规划 |
| `papers/README.md` | 相关论文阅读与边界整理 |

### 21.4 维护规则

每完成一次实验或论文级动作，必须：

1. 把完成项从 `NEXT_STEPS.md` 移到 `experiment_report.md`；
2. 如果改变了论文 claim，更新 `analysis/claim_evidence_map.md`；
3. 如果涉及命令、服务器运行、输出文件或编译，更新 `analysis/reproduction_log.md`；
4. 如果实验结果不好，不删除，写进 `EXPERIMENT_FIX_PLAN.md` 或 `experiment_report.md` 的 negative/boundary 部分；
5. 任何没有 canonical output 的数字，不进入摘要、引言和主表。
