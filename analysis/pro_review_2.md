# Overall Verdict

**当前版本：Strong Reject。不是 oral 水平，也还不是可投稿论文。**

仓库目前是一份相当成熟的研究设计文档，但不是已有方法、定理和实验证据的论文。`claim_evidence_map.md` 明确显示所有核心 claim 均为 pending，`paper.tex` 也只是格式 skeleton。

| 维度             |                        严格评分 | 判断                                                             |
| -------------- | --------------------------: | -------------------------------------------------------------- |
| 问题重要性          |                        8/10 | 真实且容易产生安全误解                                                    |
| 问题定义 sharpness |                        8/10 | “issued claims 上的 false certification”比普通 coverage 明确得多        |
| 当前 novelty     |                        4/10 | 统计核心已有 selective conformal/FCR/CRC；safe-RL 侧已有 SafeFQL/CAPS    |
| 当前理论           |                        2/10 | 关键 theorem 未定义完成，更未证明                                          |
| 当前方法           |                        2/10 | selection-aware algorithm 事实上尚不存在                              |
| 当前实验           |                        0/10 | 无代码、无结果、所有证据 pending                                           |
| 当前 oral 上限     |                           无 | 当前形态必拒                                                         |
| 大幅重构后的上限       | Strong Accept；有条件具备 oral 潜力 | 必须变成 RL-specific selective certification，而不是 conformal wrapper |

我的核心判断是：

> **“False certification among issued claims after action selection”是一个足够 sharp 的评测对象，但仅靠提出这个对象，不足以构成 oral 级 novelty。**

它在 offline safe RL 中可能是一个尚未被系统化研究的重要 gap；但在统计学层面，“选择后边际覆盖失效、需控制 selection-conditional risk/FCR/FDR”已经是成熟问题。真正能支撑 oral 的主贡献必须是：

> **在策略依赖残余成本、离线不可识别性、支持限制、候选动作块选择和序列状态漂移同时存在时，如何给出有限样本的 selective safety certification。**

---

# Fatal Risks

## 1. 叙事升级了，但方法没有升级

这是当前最大问题。

`idea_blueprint.md` 的实际方法仍然是：

1. 用 global/group conformal 得到 (U_c(s,a))；
2. 取 (U_c(s,a)\le b) 的动作；
3. 从中选择最高奖励动作。

这恰好就是文档自己已经证明会出现 post-selection failure 的流程。所谓 “selection-aware risk control / FCR correction”只出现在 pipeline 名称里，没有算法、loss、校准单位、参数选择规则或保证。

因此当前 ACCS 不是一个方法，而是一项待完成的研究任务。

**必须停止把 group/Mondrian CP 称为 ACCS 的核心。** Group conditioning 可以是 baseline 或 calibration primitive，但不能修复一般的 selection failure。

---

## 2. 三个不同 estimand 被混为一谈

当前理论在以下对象之间来回切换：

[
\rho_{\mathrm{sel}}
===================

# \Pr(F=1\mid I=1)

\frac{\mathbb E[IF]}{\mathbb E[I]},
]

即总体 deployment query distribution 上的 selective risk；

[
\operatorname{FCR}_T
====================

\mathbb E\left[
\frac{\sum_{t=1}^T I_tF_t}
{\max(1,\sum_{t=1}^T I_t)}
\right],
]

即有限流上的 false-coverage proportion 的期望；

以及

[
\Pr(F_t=1\mid I_t=1,\mathcal F_{t-1}),
]

即历史条件下的逐时风险。

三者不等价。当前 `theory_proofs.md` 同时将条件概率和 FCR 作为可替代 theorem target，这是不可接受的。

**推荐主文只选一个：**

[
\rho_{\mathrm{sel}}
===================

\Pr!\left(
Z_H^{\pi_{\rm cont}}>B
\mid \text{one action is issued}
\right).
]

FCR、time-uniform risk 和 episode risk 分别作为 extension。否则审稿人会指出你实际上没有证明 headline metric。

---

## 3. Offline identifiability 仍未解决

你想校准的是：

[
Z_H^{\pi_{\mathrm{cont}}}(s,a),
]

但普通离线轨迹给你的通常是：

[
Z_H^\beta(s,a),
]

其中 (\beta) 是行为策略。执行首动作后由 CAPS、ACCS、fallback 或新策略继续控制，都会改变 residual cost 分布。

仓库已经正确识别了这个问题，但只是列出 simulator branching、OPE、model-based target 或降级为 one-step target，没有选择其中任何一条。

Conformal OPE 的存在进一步说明，这不是普通 split conformal 能绕过的问题：行为策略和目标策略之间的分布偏移需要额外 machinery。([arXiv][1])

这里没有模糊空间：

* 使用 simulator branching：论文应称为 **simulator-assisted safety auditing**，不能暗示仅凭 offline log 就能得到 target-policy certificate。
* 使用 importance weighting/OPE：必须有 propensity、overlap 和有限方差或有界权重假设。
* 使用 learned dynamics：必须把 model uncertainty 纳入 guarantee。
* 都做不到：主 target 应降级为可观测的 one-step violation，而非 residual-horizon safety。

---

## 4. SafeFQL overlap 很重

SafeFQL 已经包含：

* offline safe RL；
* reachability-style safety value；
* deployment-time safe action selection；
* 对 learned safety boundary 的 conformal correction；
* 有限样本概率覆盖。

其校准对象更接近固定 learned policy 下的 state-level safe sublevel set，并且文中明确表示 calibration requires a fixed policy、critic 学习发生在数据支持内；它没有直接控制“从 (K) 个候选动作中选出最高奖励动作后的 issued-claim false certification”。这确实留下了 gap，但 gap 比当前叙述窄得多。([ar5iv][2])

因此：

> **ACCS 必须证明 SafeFQL 原始 calibration 在候选选择、rank selection 或 moving-budget query 后出现系统性失效，并证明 ACCS 修复的是这个特定 failure。**

否则 reviewer 的结论会是：

> “SafeFQL 的 conformal calibration，外加一个已有 selective-risk procedure。”

---

## 5. 统计学 novelty 受到 CAP、CRC 和更新工作的正面压制

CAP 已经将问题定义为 online adaptive selection 后的 selection-conditional coverage 与 FCR control。([arXiv][3])

更麻烦的是，Sale 与 Ramdas 指出若干已有 selective conformal calibration-selection 策略的保证存在根本错误，并提出保持 exchangeability 的修正策略。因此不能把 CAP 当成无需检查的“已验证 baseline”直接移植。([arXiv][4])

Vanilla CRC 控制的是 exchangeable 样本上的 monotone expected loss；你的随机分母 selective risk

[
\frac{\mathbb E[IF]}{\mathbb E[I]}
]

以及“阈值改变后选中的动作也改变”的机制，通常不天然满足其一维单调 loss 设定。([ar5iv][5])

而 2026 年的 non-monotonic CRC 已经进一步覆盖多维、非单调、稳定性依赖的 risk-control algorithm；同年还出现了 post-hoc conformal selection 与 anytime selective acting。([arXiv][6])

所以绝对不能声称：

> “We introduce calibration after action selection.”

可声称的只能是：

> “We study and solve an RL-specific instance of selective certification involving policy-dependent residual outcomes, offline support, and within-state candidate selection.”

---

## 6. 当前 target theorem 过强且定义不良

文档希望证明：

[
\sup_{g\in\mathcal G}\sup_{b\in\mathcal B}
\Pr(Z>b\mid I=1,G=g,B=b)\le \alpha.
]

主要问题：

* 对连续 (b) 做 exact conditioning，通常没有可估计意义；
* 某些 (g,b) 下 issuance probability 可能接近零，条件风险无法稳定估计；
* 若 group、budget 或 rule 根据同一 calibration set 自适应选择，会产生第二层 selection；
* 无假设的 exact conditional coverage 本身已知不可能。([arXiv][7])

应改为：

* 预注册有限 budget grid；
* 或声明 (B\sim Q_B)，控制该 query distribution 下的平均 selective risk；
* 只对 claim yield 大于 (\gamma) 的组给保证；
* group、threshold family 和 selection rule 必须在 audit labels 之外冻结。

---

## 7. Action-level guarantee 与 trajectory safety 之间仍有巨大断层

即使每个 query block 上的 selected-action risk 有保证，执行后产生的新状态分布也可能偏离 calibration distribution。

简单的

[
\sum_t\alpha_t\le \alpha_{\rm episode}
]

只有在每步保证是相对于历史 filtration 条件成立时，才能合理用于 sequential composition。边际的一步 conformal coverage 不能直接 union-bound 成有效 trajectory guarantee。

当前把 horizon 部分作为“经验审计边界”是诚实的；在没有新的 martingale/filtration theorem 前，不应把它写成理论贡献。

---

## 8. 实验很容易通过 abstention 被“作弊”

任何方法都可以通过几乎不签发 claim 来把 false certification 压低。必须同时报告：

[
(\text{selective risk},\ \text{yield},\ \text{utility},\ \text{fallback cost}).
]

而且 claim yield 必须基于所有方法共享的固定 candidate/query bank；否则方法可以通过改变 proposal policy 来人为制造更容易的 queries。

仓库对此已有认识，但所有证据仍为 pending。

---

# Novelty vs Prior Work

| Prior work                  | 已经占据的空间                                                                                        | ACCS 唯一可能存活的 gap                                                                            |
| --------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| CAPS                        | moving constraints、policy/action candidate filtering、每状态选择最高奖励 feasible policy、38-task DSRL 评测 | learned feasibility 经有限样本校准后，**被选择动作上的风险**是否仍受控 ([arXiv][8])                                |
| SafeFQL                     | reachability safety critic、one-step safe policy、conformal safety-boundary correction           | 多候选选择、budget query 与 issued-claim conditional risk，而非固定 policy state-level set ([ar5iv][2]) |
| AEGIS/BCRL                  | feasibility critics、budget-conditioned reachability、跨预算安全结构                                    | 统计证据与有限样本 false certification，而非再学一个 feasible set ([arXiv][9])                              |
| TREBI                       | offline RL 下 deployment-time real-time budget                                                  | moving budget 本身不能作为 novelty ([arXiv][10])                                                  |
| RPS                         | 从离线数据构造高概率安全 shield                                                                            | 连续高维、cumulative-cost、selective risk 与 support-aware audit ([arXiv][11])                     |
| CAP / selective conformal   | 选择后的 conditional coverage/FCR                                                                  | Markov、off-policy、candidate-block 与 residual-cost identification                            |
| CRC                         | 一般 expected risk control                                                                       | 随机分母、动作重选、nonmonotone rule、off-policy weighting                                             |
| Conformal OPE               | target/behavior policy shift下的区间估计                                                             | 每个 state-candidate block 的 selective safety claim                                           |
| Conditional-coverage limits | 无假设下 pointwise conditional validity 不可能                                                        | 明确可实现的 group/query-distribution validity                                                    |

### 对核心问题定义的最终判断

**Sharp：是。**

它明确区分了：

[
\Pr(Z\le U)
]

和

[
\Pr(Z>b\mid U\le b,\ a=\text{selected}).
]

这个区分是真实、可检验、对部署有意义的。

**统计意义上的新：不是。**

选择后错误集中、FCR/FDR、selective risk control 都已有体系。

**Offline safe RL 意义上的潜在新：有，但尚未建立。**

需要同时满足：

1. 第一次系统展示强 OSRL 方法上的 selection amplification；
2. 给出 policy-specific/off-policy 的正式理论；
3. 给出 support impossibility；
4. 给出直接控制 selected-action risk 的新算法或明显更适配 RL 的 theorem；
5. 在 CAPS、SafeFQL 等强 proposer 上成立，而不仅是自建弱 policy。

另有一个必须立即消歧的问题：repo 的 `CAPS` 是 **Constraint-Adaptive Policy Switching**，而你在任务中写了 **Conformal Action Prediction Sets**。当前 `paper_index.csv` 没有后者的明确条目。若它是另一篇工作，当前 threat map 仍漏掉了直接 prior。

---

# Theory Upgrade Plan

## 现有命题处理

| 当前内容                               | 判决             | 处理                                                  |
| ---------------------------------- | -------------- | --------------------------------------------------- |
| Group-marginal conformal coverage  | 正确但标准          | 附录 lemma                                            |
| Selection can concentrate failures | 正确方向，只有 sketch | 写成 exact amplification theorem                      |
| Policy-specific residual target    | 当前只是明显事实       | 升级为 observational non-identifiability theorem       |
| No-overlap impossibility           | 有潜力，但目前接近口头论证  | 写成两 CMDP indistinguishability/minimax lower bound   |
| Selection-aware control target     | 尚未有 theorem    | 必须成为主 theorem                                       |
| Budget monotonicity                | 一行集合包含         | 从 contribution 删除                                   |
| Granularity trade-off              | 经验假设           | 作为 ablation                                         |
| Horizon union bound                | 太弱且可能误用        | 要么改成 filtration-conditional theorem，要么仅留 limitation |

仓库自身已经基本承认前三项的状态。

## 建议的正式 statistical unit

不要把每个 candidate action 当作独立 exchangeable sample。单位应是整个 deployment query block：

[
W_i=
\left(
S_i,B_i,
{A_{ij},\widehat Q^r_{ij},\widehat Q^c_{ij}}*{j=1}^{K_i},
{Z^{\pi*{\rm cont}}*{ij}}*{j=1}^{K_i}
\right).
]

不同 block 独立或 exchangeable；同一 block 内候选动作可以高度相关。

给定 issuance/selection rule (h)：

[
I_h(W)=\mathbf 1{h\text{ issues an action}},
]

[
F_h(W)=
\mathbf 1{
h\text{ issues }j^\star,,
Z^{\pi_{\rm cont}}_{j^\star}>B
}.
]

主目标：

[
\rho(h)=\frac{\mathbb E[F_h]}{\mathbb E[I_h]},
\qquad
\mathbb E[I_h]\ge\gamma.
]

最低 yield 条件 (\gamma) 必须写进 theorem；否则条件风险可能通过零发行率被平凡满足。

## 推荐 theorem stack

### Theorem 1：Selection Amplification

构造每个候选 marginal failure probability 为 (p)，选择 rule 总能优先选 failure-correlated 高 reward action，则

[
\rho_K=1-(1-p)^K.
]

因此即使 (p<\alpha)，(\rho_K\to1) 随 (K) 增大。这是 Figure 1 theorem，但不能单独支撑 oral。

### Theorem 2：Offline Non-identifiability / No-overlap

构造两个 CMDP (M_0,M_1)：

* 在行为 occupancy support 上 transition/cost 完全相同；
* 在 queried unsupported action (a^\star) 后，(M_0) residual cost 为 0，(M_1) 为 1。

它们诱导完全相同的离线数据分布。任何在 (a^\star) 上以正概率签发“安全”声明的算法，在 (M_1) 中 conditional false-certification risk 为 1。

进一步可做 approximate-overlap 版本：

[
\text{false-issue lower bound}
\ge
\text{claim yield}
------------------

\operatorname{TV}(P_{M_0}^n,P_{M_1}^n).
]

这才是真正给 abstention 数学地位的主 negative result。

### Theorem 3：有限样本 selective-risk control

设预注册有限规则族 (\mathcal H)，独立 audit blocks 数量为 (n)。令

[
\widehat f_h=\frac1n\sum_i F_h(W_i),
\qquad
\widehat i_h=\frac1n\sum_i I_h(W_i),
]

以及

[
\epsilon_n=
\sqrt{
\frac{\log(4|\mathcal H|/\delta)}{2n}
}.
]

若选择满足

[
\widehat i_h>\epsilon_n,
\qquad
\frac{\widehat f_h+\epsilon_n}
{\widehat i_h-\epsilon_n}
\le\alpha,
]

的最高 utility rule，则用 uniform concentration 可直接得到：以至少 (1-\delta) 的概率，

[
\rho(h)\le\alpha.
]

这是真正控制 headline estimand 的简单、清晰、reviewer-proof 起点。随后可用 empirical-Bernstein、confidence sequence 或 e-process 提高效率。

它不一定非要叫 conformal。**如果保证本质是 uniform risk bound，就不要为了 branding 强行称 conformal。**

### Theorem 4：Off-policy extension

对 calibration law (P) 和 deployment query law (Q)：

[
\rho_Q(h)=
\frac{\mathbb E_P[w(W)F_h(W)]}
{\mathbb E_P[w(W)I_h(W)]},
\qquad
w=\frac{dQ}{dP}.
]

在 (w\le W_{\max}) 或有效 ESS 下给 weighted concentration guarantee；当 density ratio 不存在、过大或无法估计时必须 abstain。

这会把工作从“选择后 CP 应用”升级为真正 RL-specific 的 **selective off-policy certification**。

### 必须禁止的 claims

* “valid for any unseen budget”
* “individual-action guarantee”
* “distribution-free deployment safety”
* “action-level validity implies trajectory safety”
* “purely offline certificate”，若标签来自 simulator branching
* “CAP provides a settled exact baseline”，除非处理后续错误分析
* “first calibration after selection”
* “ACCS controls FCR”，除非 theorem 确实控制有限流 FCR，而非 population conditional risk

---

# Exact Toy Experiment

## 环境

一个一步终止 CMDP：

* 唯一初始状态：(s_0)
* 每个 query 采样 (K) 个 candidate actions：
  [
  x_j\overset{\text{i.i.d.}}{\sim}\operatorname{Unif}[0,1],
  \qquad a_j=a(x_j)
  ]
* reward：
  [
  r(a_j)=x_j
  ]
* residual cost：
  [
  Z(a_j)=\mathbf 1{x_j>0.96}
  ]
* budget：
  [
  b=0.5
  ]
* learned cost predictor：
  [
  \widehat Q_c(s_0,a)=0.
  ]

因此 nonconformity residual 为 (e=Z)。在 (\alpha=0.05) 时，population (95%) quantile 是 0，因为 96% proposals 的 cost 为 0。

用 (n_{\rm cal}=1999) 的实际 split conformal，(q=0) 的概率约为 98.49%；当 (q=1) 时不签发任何 claim。应同时报告无条件结果和条件于 issuance 的结果。

## Selection rule

所有 (U_j=0\le b) 的动作都被普通 CP 认证，然后执行：

[
j^\star=\arg\max_j r(a_j)=\arg\max_j x_j.
]

每个 proposal 的 marginal false rate 是 4%，低于 nominal 5%；但 selected action 的 false certification 是：

[
\rho_K
======

# \Pr\left(\max_jx_j>0.96\right)

1-0.96^K.
]

| (K) | Proposal marginal error | Selected false certification |
| --: | ----------------------: | ---------------------------: |
|   1 |                   4.00% |                        4.00% |
|   2 |                   4.00% |                        7.84% |
|   4 |                   4.00% |                       15.07% |
|   8 |                   4.00% |                       27.86% |
|  16 |                   4.00% |                       47.96% |
|  32 |                   4.00% |                       72.92% |

这张表足以成为真正的 Figure 1 左半部分。

## Selection-aware rule

定义规则族：

[
h_\tau:
\quad
\text{只允许 }x_j\le\tau,\quad
\text{再选其中最大 reward 动作}.
]

用独立 tune/audit query blocks，通过前述 ratio-UCB 选取最大可认证 (\tau)。

Oracle (\tau^\star=0.96) 时，在 (K=16)：

* false certification：0；
* claim yield：
  [
  1-0.04^{16}\approx1;
  ]
* unconstrained expected reward：
  [
  \mathbb E[\max_jx_j]=16/17\approx0.941;
  ]
* capped selected reward约为 0.901；
* 相对 reward loss 约 4.25%。

因此这个 toy 不会靠“几乎全部 abstain”作弊。

## Baselines

必须包括：

1. uncalibrated cost score；
2. global split CP；
3. Mondrian CP，group 与 (x) 独立；
4. reward-bin/group CP；
5. Bonferroni (\alpha/K)；
6. calibration on selected blocks；
7. vanilla CRC，仅在验证 monotonicity 后使用；
8. CAP implementation；
9. Sale–Ramdas 修正后的 exchangeability-preserving selective conformal；
10. proposed selective-risk UCB/ACCS；
11. oracle (\tau^\star)。

其中 reward-bin CP 是非常重要的强 baseline：若它已经完全解决问题，ACCS 不能再把“selection awareness”当成独立算法 novelty。

## Metrics

* proposal marginal coverage；
* (\Pr(F=1\mid I=1))；
* finite-stream FCR；
* FDP 超过 (\alpha) 的概率；
* claim yield；
* selected reward；
* utility at controlled risk；
* fallback rate/reward/cost；
* calibration sample size和有效 support；
* risk–coverage curve。

## 两个扩展 panel

**Policy mismatch panel：** 两步 MDP 中，behavior policy 在第二步总是 rescue，deployment policy 总是 exploit。离线 residual cost 全为 0，但 deployment residual cost 在高 (x) 状态为 1。

**No-overlap panel：** calibration 数据完全不含 (x>0.9)。构造两个在 observed support 上相同、在 (x>0.9) 上 cost 相反的 MDP；展示 valid method abstain，而强行签发的方法在其中一个 world 必然失败。

---

# Main Benchmark Plan

## 1. 环境选择

第一阶段选择同时覆盖 SafeFQL 与 DSRL/CAPS 的任务：

* Hopper Safe-Velocity
* Walker2d Safe-Velocity
* HalfCheetah Safe-Velocity
* Ant Safe-Velocity
* PointGoal 或 CarGoal，用于可视化 action selection

SafeFQL 本身在 Hopper、HalfCheetah、Swimmer、Walker2d、Ant Safe-Velocity 上评测，因此至少应覆盖其中三项。([ar5iv][2])

最终 oral 版本应扩展到接近 CAPS 的 DSRL 广度，而不是只挑 2–3 个有利环境。CAPS 已经报告 38 个 DSRL 任务；过窄 benchmark 会显得明显回避。([arXiv][8])

## 2. Proposal families

* **CAPS:** 每个 policy 的动作构成 candidate bank。
* **SafeFQL:** 对 latent noise 采样 (K) 个 one-step flow actions。
* **FISOR 或其他 generative OSRL:** 采样 (K) 个候选动作。
* **CPQ/COptiDICE/BCQ-Lag:** 单 policy action 加预注册 perturbation/proposal mechanism。

所有 auditor 必须使用相同：

[
(s,\ b,\ {a_1,\dots,a_K})
]

query bank，不能各自改变 proposal distribution。

## 3. Auditor matrix

不要把所有 OSRL 方法与所有 auditor 做笛卡尔积。主矩阵应是：

| Base proposer | Auditor                                                                           |
| ------------- | --------------------------------------------------------------------------------- |
| CAPS          | none / global CP / group CP / selected-block CP / valid selective baseline / ACCS |
| SafeFQL       | original calibration / original+post-selection audit / ACCS                       |
| FISOR 或 CPQ   | none / global CP / ACCS                                                           |

## 4. Ground-truth protocol

按 trajectory，而非 transition，划分：

* train；
* calibration/tuning；
* independent audit；
* test。

对每个 test query：

1. 保存 simulator state；
2. 执行 candidate action；
3. 按明确的 (\pi_{\rm cont}) 继续；
4. 在随机环境中运行 32–128 个 branch rollouts；
5. 得到真实 residual violation probability 或 residual-cost distribution。

主文必须称其为 simulator-ground-truth evaluation。若校准本身也使用这些 branch rollouts，则方法不是纯 offline-log certifier。

## 5. Budget protocol

不要直接跨任务使用任意 `{3,5,8,12,...}`。使用归一化 residual budget：

[
b\in
{0.5,0.75,1.0,1.25,1.5}
\times b_{\rm benchmark}.
]

分开测试：

* 固定 (B\sim Q_B)；
* interpolation；
* extrapolation；
* predictable adaptive budget stream。

自适应 budget 若依赖模型输出，本身又是一个 selection mechanism，必须单独校准。

## 6. Primary metrics

主表只需要六组：

1. issued-claim selective risk，并带置信区间；
2. target risk 是否满足；
3. claim yield；
4. normalized reward / utility at controlled risk；
5. episode violation probability与超额幅度；
6. fallback rate、reward 和 cost。

平均 episode cost 不能代替 violation probability。

## 7. 必做 ablations

* (K\in{1,2,4,8,16,32})
* candidate calibration vs selected-block calibration
* matched vs mismatched continuation policy
* calibration size
* budget grid size
* group granularity
* support threshold / effective sample size
* no support abstention
* same-data tuning vs independent audit
* SafeFQL original calibration vs post-selection correction
* fallback controller
* initial-state、proposal-policy 与 dynamics shift

---

# Paper Narrative Rewrite

## 推荐标题

> **Calibration After Action Selection: Selective Safety Certification for Offline Reinforcement Learning**

先删除 “under Moving Budgets”。Moving budgets 已被 CAPS、TREBI、BCRL 等占据，应作为重要 stressor，而不是标题里的主要 novelty。

## Core Contributions

1. **Problem and estimands.**
   We formalize selective safety certification in offline RL and distinguish proposal-level marginal coverage, false certification conditional on issuing an action, finite-stream FCR, and trajectory-level safety.

2. **Fundamental limits.**
   We give an exact selection-amplification construction and prove that target-policy residual safety is not identifiable for unsupported actions from offline behavior data; any uniformly valid certifier must abstain there.

3. **Selection-aware certification.**
   Under block-exchangeable deployment queries, a declared continuation policy, valid target-policy labels, and minimum-yield conditions, we develop a support-aware auditor with finite-sample control of selective false-certification risk over a prespecified rule class.

4. **Auditing strong offline safe-RL systems.**
   Using common proposal banks, we evaluate CAPS, SafeFQL, and standard OSRL proposers, measuring selective risk, claim yield, utility, fallback behavior, and episode-level consequences jointly.

在真正得到 theorem 和结果前，不要把第 3、4 条写进投稿 abstract。

## Abstract

> Offline safe reinforcement learning systems increasingly choose deployment actions by thresholding learned cost, reachability, or feasibility scores, sometimes after conformal calibration. A marginal guarantee over proposed actions, however, is not a guarantee for the action that a deployment rule ultimately selects. We formalize this distinction as selective false certification: the probability that a residual-cost claim is false conditional on issuing and executing an action, for a declared proposal mechanism, budget-query distribution, and continuation policy. We exhibit a finite CMDP in which proposal-level coverage is 96%, yet selecting the best of 16 apparently certified actions raises false certification to 48%. We further show that residual-cost claims are policy-specific and that unsupported actions are not distribution-free certifiable from offline data. Under block-exchangeable deployment queries and valid target-policy labels, we introduce a support-aware auditing procedure that controls selective false-certification risk over a prespecified certification-rule class and abstains when evidence is insufficient. Across [TASKS], wrapping CAPS, SafeFQL, and [BASELINE] restores the target risk while retaining [YIELD] claim yield and [UTILITY] task performance. These results show that calibrating a safety score and certifying a selected action are different statistical problems.

## Intro narrative

**Paragraph 1：先承认 prior。**
现有 OSRL 方法已经能够学习 feasible actions、适配不同预算，并进行 deployment-time filtering。不要先树稻草人。

**Paragraph 2：提出缺失的 estimand。**
这些方法通常验证 learned score 或 aggregate episode cost，但部署系统实际执行的是经过 reward ranking、budget filtering 和 fallback 逻辑选择后的动作。

**Paragraph 3：给出反直觉 failure。**
95–96% marginal coverage 可以在 (K=16) 的最高奖励选择后变成约 48% false certification。

**Paragraph 4：指出 RL 特有障碍。**
selected label 取决于 continuation policy；离线数据未必识别它；无 overlap 时任何非平凡 certificate 都不可信。

**Paragraph 5：方法与保证。**
定义固定 proposal/query block，直接控制 selective risk，并将 support insufficiency 转化为正式 abstention。

**Paragraph 6：实验。**
直接包装 CAPS、SafeFQL 和标准 OSRL；报告 risk、yield、utility、fallback 与 episode risk，而非只报告 reward/cost。

`U/C/A/H` 四轴可以留在 discussion 或 evaluation checklist，不应在 intro 占据大量篇幅。当前论文最需要的是一个 estimand、一条 theorem、一张主现象图，而不是新的概念 taxonomy。

---

# 7-Day Execution Plan

这七天应被定义为 **go/no-go research sprint**，不是完整 AAAI benchmark 周。

| Day | 任务                                    | 当日产物与 kill criterion                                                                                                                   |
| --- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 冻结 estimand 与理论单位                     | 写出 block-level setup、(\rho_{\rm sel})、FCR 区分；删除 `sup_b` 空泛 theorem；补 CAP critique、nonmonotonic CRC、CSA、post-hoc selection；消歧两个 CAPS    |
| 2   | 实现 exact toy                          | `toy_selection_failure.py`；闭式 (1-(1-p)^K) 单元测试；Figure 1 左图、Table 1；若 (K) amplification 不稳定，立即停                                         |
| 3   | 实现 valid selective baseline 与 ACCS-v0 | global/group CP、selected-block CP、Bonferroni、ratio-UCB、CAP/修正版；输出 risk–yield–reward frontier；若 valid baseline 完全支配 ACCS，承认没有方法 novelty |
| 4   | 写理论与第二组 toy                           | 完成 amplification theorem、两-CMDP no-overlap theorem、policy-mismatch toy、finite-family risk theorem；形成可编译 theory note                    |
| 5   | CAPS 单任务集成                            | 在一个 DSRL/Safe-Velocity 任务冻结 query bank；生成 CAPS candidate actions；实现 state restore 和 continuation rollout evaluator                     |
| 6   | SafeFQL/第二 proposer pilot             | 至少一个 SafeFQL overlap task；跑 (K)、budget、support、calibration-size ablation；5 seeds；比较 original calibration 与 post-selection audit        |
| 7   | 审稿式收口                                 | 生成真实 Figure 1、risk–coverage figure、toy table、pilot table；重写 title/abstract/intro；更新 claim-evidence map；按 kill criteria 决定继续或 pivot     |

第七天必须做出明确决策，而不是继续扩大代码工程。

### Go criteria

* (K=16,\alpha=0.05) 时 global/group CP 的 selected risk 至少达到 20–30%；
* valid ACCS 控制到约 5%，而非只在平均意义上看起来较低；
* supported region claim yield 至少 70%；
* reward loss最好低于 10%；
* effect 在 CAPS 或 SafeFQL 上仍出现；
* common query bank 后结果不消失；
* independent audit 后结果不消失。

### No-go criteria

* 只有故意设计的 toy predictor 才出现 failure；
* reward/rank-conditioned CP 已完全解决；
* ACCS 仅靠超过 50% abstention 达标；
* SafeFQL 原始 calibration 已达到同等 selected risk；
* target labels只能通过强 simulator oracle 获得，但论文仍想声称纯 offline certification；
* action-level metric改善，却没有任何 episode-level后果。

---

# Final Recommendation

**不要以当前 ACCS 形态继续扩展 Safety-Gym/DSRL。**

当前路线中最弱的版本：

> group CP + budget threshold + highest-reward action + abstention

只是一个增量 conformal shield，且并不解决论文自己提出的 selection failure。即使实验好看，也很难达到顶会 oral；面对 SafeFQL、CAPS、CRC 与 selective conformal，regular accept 都不稳。

最强且值得继续的替代路线是：

> **Support-Aware Selective Off-Policy Certification for Offline RL**

其论文骨架应是：

1. selection amplification 作为主现象；
2. target-policy residual-cost non-identifiability 作为第一个主 theorem；
3. no-overlap claim-yield lower bound 作为第二个主 theorem；
4. block-level finite-sample selective-risk control 作为正面 theorem；
5. bounded density-ratio/off-policy extension；
6. CAPS、SafeFQL 上的直接 audit；
7. moving budgets 作为 selection stressor，而非核心 novelty。

**最终判决：核心现象值得做，但当前方法不值得直接做。保留 thesis，重写 estimand，替换算法和 theorem。**

[1]: https://arxiv.org/abs/2304.02574 "https://arxiv.org/abs/2304.02574"
[2]: https://ar5iv.org/html/2603.15136v1 "https://ar5iv.org/html/2603.15136v1"
[3]: https://arxiv.org/abs/2403.07728 "https://arxiv.org/abs/2403.07728"
[4]: https://arxiv.org/abs/2503.16809 "https://arxiv.org/abs/2503.16809"
[5]: https://ar5iv.labs.arxiv.org/html/2208.02814 "https://ar5iv.labs.arxiv.org/html/2208.02814"
[6]: https://arxiv.org/abs/2602.20151 "https://arxiv.org/abs/2602.20151"
[7]: https://arxiv.org/abs/1903.04684 "https://arxiv.org/abs/1903.04684"
[8]: https://arxiv.org/abs/2412.18946 "https://arxiv.org/abs/2412.18946"
[9]: https://arxiv.org/abs/2603.22292 "https://arxiv.org/abs/2603.22292"
[10]: https://arxiv.org/abs/2306.00603 "https://arxiv.org/abs/2306.00603"
[11]: https://arxiv.org/abs/2605.10293 "https://arxiv.org/abs/2605.10293"
