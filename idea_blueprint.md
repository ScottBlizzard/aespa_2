# AAAI_2 Oral-Ambition Blueprint

> Version: 2026-06-24
> Target: AAAI 2027 / ICLR-style trustworthy RL, safe decision making, conformal risk control
> Current phase: trained-proposer evidence building, not submission polish
> Principle: use harsh reviews to raise the paper's ceiling, not to shrink the idea before evidence exists

---

## 0. North Star

This project should not be framed as a small conformal wrapper for offline safe RL. The high-ceiling thesis is:

> **When a deployed safe-RL system selects actions using learned safety scores, the safety certificate itself enters the decision loop. Calibration before selection is not calibration after selection.**

The paper should make a sharp distinction between three objects:

```text
1. A learned cost or feasibility score.
2. A deployment-time action selected using that score.
3. A safety certificate issued for the selected action.
```

Existing offline safe RL methods can learn feasible actions, adapt to budgets, construct shields, or calibrate a learned safety boundary. That does not settle the certificate question:

```text
Among the actions that the system actually certifies and executes,
how often are the safety claims false?
```

The oral-level opportunity is to turn this into a new evaluation and certification protocol for offline safe RL:

```text
Support-aware selective safety certification for offline RL.
```

This is not a decision to make the paper smaller. It is the opposite: the project should become a full research program around deployment-time safety claims, with several possible attack paths. Experiments will determine which path becomes the final paper.

---

## 1. Core Thesis

### 1.1 One-Sentence Thesis

> **A safety score is not a safety certificate: offline safe-RL systems need support-aware, selection-aware calibration for the actions they actually certify and execute.**

### 1.2 Reviewer-Facing Thesis

Offline safe reinforcement learning systems increasingly select deployment actions by thresholding learned cost, reachability, or feasibility scores. These scores may be accurate on average, and may even be marginally calibrated before action selection. However, deployment systems do not execute random proposed actions. They filter actions by budget, rank them by reward, fall back when evidence is weak, and repeatedly query the same learned critic under changing constraints. This selection process can concentrate calibration errors exactly among the actions that receive safety certificates.

The paper studies this missing statistical object: **false certification among issued action claims**. The goal is not to replace strong offline safe-RL optimizers such as CAPS, BCRL, AEGIS, RPS, or SafeFQL. The goal is to audit whether their selected actions support finite-sample safety claims under the actual deployment protocol.

### 1.3 The Slogan

Use one of these in the title or introduction:

```text
A safety score is not a certificate.
```

```text
Calibration before selection is not calibration after selection.
```

```text
Safe action learning is not safe action certification.
```

---

## 2. Working Titles

Highest-ceiling title:

> **A Safety Score Is Not a Certificate: Selective Safety Certification for Offline Reinforcement Learning**

More technical title:

> **Calibration After Action Selection: Support-Aware Certification for Offline Reinforcement Learning**

More systems-facing title:

> **When Safety Certificates Choose Actions: Auditing Deployment-Time Action Selection in Offline Safe RL**

Moving budgets should remain an important stressor and experiment axis, but should not be the only headline novelty because CAPS, TREBI, BCRL, and related work already occupy much of the moving-constraint space.

---

## 3. What Makes This Potentially Oral-Level

The project has oral potential only if it becomes more than "add conformal prediction to safe RL." The paper should aim for a package with five mutually reinforcing pieces:

| Pillar | Oral-level version | Why it matters |
|---|---|---|
| Phenomenon | Selection amplification: marginally calibrated proposals become miscalibrated selected claims | memorable Figure 1 |
| Formal target | False certification among issued action claims | a new deployment evidence object |
| Limits | Policy-specific residual cost and no-overlap impossibility | prevents overclaiming and gives theory depth |
| Method | Support-aware selective auditor over fixed proposal/query blocks | method is not just group CP |
| Strong evaluation | Direct audit of CAPS/SafeFQL-style proposers | survives prior-work pressure |

The harsh reviews are useful because they identify what must be added for the paper to reach that ceiling. They should not be read as a reason to collapse the project into a conservative note.

---

## 4. Prior Work Pressure as an Upgrade Map

The strongest prior work does not kill the idea. It tells us which weak claims are unavailable and where the strongest contribution must live.

| Prior line | What it already owns | What AAAI_2 can still own |
|---|---|---|
| CAPS | constraint-adaptive policy switching, action filtering, DSRL-scale evaluation | whether selected CAPS actions carry calibrated finite-sample certificates |
| SafeFQL | reachability-style safety value, safe action selection, conformal boundary calibration | whether fixed-policy safety-boundary calibration survives multi-candidate action selection and budget queries |
| BCRL / AEGIS | budget-conditioned reachability and feasible-action structure | statistical reliability of issued claims under finite data and support limits |
| RPS / safety shielding | high-probability shielding from offline data | continuous/action-bank selective risk and support-aware abstention |
| CAP / selective conformal | post-selection coverage and FCR in statistical settings | RL-specific residual outcomes, candidate blocks, continuation policy, off-policy support |
| CRC | expected risk control for monotone losses | random-denominator selective risk, nonmonotone action selection, off-policy query laws |
| Conformal OPE | target/behavior policy shift for intervals | action-claim certification over selected query blocks |

The project should explicitly concede that action-feasibility learning is prior work. The new question is evidence and certification after a deployment rule selects an action.

Important terminology check:

```text
CAPS in this repo means Constraint-Adaptive Policy Switching.
If another "Conformal Action Prediction Sets" paper is relevant, it must be added separately.
```

---

## 5. Formal Problem Object

### 5.1 Deployment Query Block

The statistical unit should be a deployment query block, not a single isolated action:

```text
W = (S, B, {A_j, Rhat_j, Chat_j, support_j}_{j=1}^K,
     {Z_j^{pi_cont}}_{j=1}^K)
```

where:

- `S` is the deployment state;
- `B` is the requested residual budget;
- `{A_j}_{j=1}^K` is a candidate action bank from a proposer;
- `Rhat_j` and `Chat_j` are reward and cost or feasibility scores;
- `support_j` records evidence quality or overlap;
- `Z_j^{pi_cont}` is the residual cost after taking `A_j` and following a declared continuation policy.

The block view matters because deployment selection happens inside the block. Candidate actions in the same block are not independent evidence units.

### 5.2 Issuance and Failure

Let a certification rule `h` take a query block and either issue a certificate for one action or abstain:

```text
h(W) in {1, ..., K, abstain}
```

Define:

```text
I_h(W) = 1{h(W) != abstain}
```

```text
F_h(W) = 1{h issues action j and Z_j^{pi_cont} > B}
```

The headline population target is:

```text
rho(h) = E[F_h(W)] / E[I_h(W)]
```

This is the false-certification risk among issued action claims under the deployment query distribution.

Finite-stream FCR, history-conditional risk, and episode-level safety are important extensions. They should not be mixed with `rho(h)` unless the theorem specifically controls them.

### 5.3 Minimum Yield

Any certification method can reduce false certification by refusing nearly all claims. Therefore every theorem and table must pair risk with yield:

```text
yield(h) = E[I_h(W)]
```

A useful method must satisfy both:

```text
rho(h) <= alpha
yield(h) >= gamma
```

and should report utility/fallback behavior at the same time.

---

## 6. Oral-Ambition Research Paths

This project should keep multiple high-upside paths alive until experiments identify the strongest one.

### Path A: Selection Amplification as the Main Phenomenon

**Claim.** A learned safety score can be marginally calibrated over proposed actions, yet produce high false-certification risk among selected actions.

**Theory.** Construct a query block with `K` candidate actions, each with marginal failure probability `p`, where the selection rule chooses a reward-correlated failure. Then:

```text
rho_K = 1 - (1 - p)^K
```

Even if `p < alpha`, selected-action false certification grows quickly with `K`.

**Experiment.** One-step exact CMDP with `x_j ~ Uniform[0,1]`, reward `r=x`, violation `Z=1{x>0.96}`, budget `B=0.5`, and a learned cost predictor that assigns zero cost to all actions. Proposal-level error is 4%, but selected-action error is `1 - 0.96^K`.

**Success signal.** A clean Figure 1 and Table 1 where global/group CP are nominal before selection and fail after selection.

**Risk.** A strong rank-conditioned baseline may fix the toy. That is acceptable: it tells us the final method must beat or generalize that baseline.

### Path B: Support-Aware Selective Certification

**Claim.** The right positive method is not group CP. It is a support-aware auditor over a prespecified family of certification rules, chosen using independent audit blocks.

**Method seed.** Define a finite rule family `H`, for example thresholds over support score, cost upper bound, candidate rank, budget bin, and fallback rule. For each `h in H`, estimate:

```text
fhat_h = n^{-1} sum_i F_h(W_i)
ihat_h = n^{-1} sum_i I_h(W_i)
```

Use a uniform confidence bound:

```text
rho_UCB(h) = (fhat_h + eps_h) / max(ihat_h - eps_h, tiny)
```

Select the highest-utility rule with:

```text
rho_UCB(h) <= alpha
ihat_h >= gamma
```

**Success signal.** The method controls selected-claim risk while preserving useful yield and reward, and does not rely on massive abstention.

**Risk.** If a generic selective-risk baseline dominates, the paper becomes a problem/benchmark/theory paper rather than a new algorithm paper. That can still be strong if the phenomenon and OSRL audit are compelling.

### Path C: Offline Identifiability and No-Overlap Limits

**Claim.** Residual-cost certificates are policy-specific and cannot be obtained for unsupported actions from ordinary offline logs without additional assumptions.

**Theory.** Construct two CMDPs that agree on the behavior-policy data distribution but differ after an unsupported action or under a different continuation policy. Any algorithm that certifies unsupported actions with nonzero probability must fail in one of the worlds.

**Experiment.** Two-step policy-mismatch panel:

- behavior continuation always rescues;
- deployment continuation exploits;
- offline residual cost appears safe;
- deployment residual cost is unsafe for high-risk actions.

**Success signal.** A sharp theorem plus a toy panel showing why support-aware abstention is not conservatism but a mathematical requirement.

**Risk.** If the final method depends heavily on simulator branching, the paper must call itself simulator-assisted auditing instead of pure offline certification.

### Path D: Auditing Strong Safe-RL Systems

**Claim.** The phenomenon is not an artifact of a toy predictor. It now appears
under a frozen official-DSRL query-bank/auditor contract for trained CAPSIQL,
CPQ, and COptiDICE checkpoint proposers.

**Experiment.** Freeze query banks:

```text
(s, B, {a_1, ..., a_K})
```

Run the same auditor variants on top of:

- CAPSIQL checkpoint candidate actions;
- standard OSRL proposer checkpoints such as CPQ and COptiDICE;
- SafeFQL sampled or flow-generated actions only if the code path can be made
  comparable under the same fixed query-bank and residual-label contract.

**Main comparison.**

| Base proposer | Auditor variants |
|---|---|
| CAPSIQL checkpoint | none, global CP, reward-bin, CRC-style, ACCS |
| CPQ checkpoint | none, global CP, reward-bin, CRC-style, ACCS |
| COptiDICE checkpoint | none, global CP, reward-bin, CRC-style, ACCS |
| SafeFQL, if comparable | original calibration, original plus post-selection audit, ACCS |

**Success signal.** Original systems show selected-claim reliability gaps;
post-selection auditors reduce issued-claim risk with acceptable yield, and
global candidate CP is exposed as low-yield rather than a practical competitor.

**Risk.** Reward-bin and CRC-style auditors are strong. The final paper should
therefore argue for the RL-specific query-block protocol and support-aware
certificate target, not a blanket claim that one auditor dominates all baselines.

### Path E: Sequential Deployment and Horizon Risk

**Claim.** Action-level certification and trajectory safety are different, but the gap itself is scientifically important.

**Theory option.** A filtration-conditional or confidence-sequence extension that controls a finite stream of issued claims.

**Experiment option.** Empirical horizon audit: false certification at action level, episode violation probability, cumulative exceedance magnitude, and fallback burden over time.

**Success signal.** The paper can explain when action certificates compose and when they do not.

**Risk.** Sequential guarantees can become too ambitious. Keep this as an extension unless the first four paths are already strong.

---

## 7. Method Portfolio

The method section should not present a single fragile algorithm too early. It should present a ladder of increasingly ambitious auditors and let experiments determine which one becomes the final ACCS.

### 7.1 Calibration Primitives

These are baselines or ingredients, not the main contribution:

```text
global split conformal
Mondrian/group conformal
reward-bin or rank-bin conformal
Bonferroni alpha/K correction
vanilla conformal risk control
selected-block calibration
CAP/FCR-style selective baselines
```

The blueprint must stop treating group CP as the core method. Group CP can reduce heterogeneity, but it does not generally solve post-selection false certification.

### 7.2 ACCS-v0: Finite-Rule Selective Auditor

ACCS-v0 is the first concrete method target:

```text
Input:
  frozen proposal/query blocks
  independent audit labels Z_j^{pi_cont}
  finite rule family H
  target alpha
  minimum yield gamma

For each h in H:
  estimate issued failures F_h
  estimate issuance I_h
  compute upper confidence bound on E[F_h]/E[I_h]

Select:
  highest utility h satisfying risk and yield constraints

Deploy:
  issue certificate only when h issues
  otherwise abstain or fallback
```

This method is not "just conformal." It is a selective-risk auditor. Conformal bounds can be features used by the rules, but the final guarantee targets issued-claim risk.

### 7.3 ACCS-v1: Support-Aware Off-Policy Auditor

ACCS-v1 adds support and distribution-shift machinery:

```text
support score
density-ratio or effective-sample-size diagnostic
abstention under weak overlap
weighted risk estimation when Q != P
```

The core target under deployment law `Q` is:

```text
rho_Q(h) = E_P[w(W) F_h(W)] / E_P[w(W) I_h(W)]
```

where `w=dQ/dP`, when it exists and can be bounded or estimated.

### 7.4 ACCS-v2: Strong-System Wrapper

ACCS-v2 wraps strong safe-RL systems:

```text
CAPS -> candidate bank -> ACCS audit
SafeFQL -> candidate bank -> ACCS audit
BCRL/AEGIS/RPS-style score -> ACCS audit
```

The point is not to beat these systems as optimizers. The point is to test whether their selected actions support calibrated deployment claims.

---

## 8. Exact Toy Experiment

The first experiment should be exact and closed-form. It must not depend on simulator complexity.

### 8.1 Construction

One-state one-step CMDP:

```text
S = s0
x_j ~ Uniform[0,1]
a_j = a(x_j)
r(a_j) = x_j
Z(a_j) = 1{x_j > 0.96}
B = 0.5
Chat(s0,a_j) = 0
```

With `alpha=0.05`, proposal-level marginal false rate is 4%, so a marginal calibrator can appear valid.

Deployment selects the highest-reward certified action:

```text
j* = argmax_j x_j
```

Selected false certification is:

```text
rho_K = P[max_j x_j > 0.96] = 1 - 0.96^K
```

Expected table:

| K | proposal false rate | selected false certification |
|---:|---:|---:|
| 1 | 4.00% | 4.00% |
| 2 | 4.00% | 7.84% |
| 4 | 4.00% | 15.07% |
| 8 | 4.00% | 27.86% |
| 16 | 4.00% | 47.96% |
| 32 | 4.00% | 72.92% |

This is the cleanest first figure.

### 8.2 Nontrivial Repair

A selection-aware rule family:

```text
h_tau:
  allow only actions with x_j <= tau
  choose highest reward among allowed actions
```

An oracle `tau=0.96` gives zero false certification with high yield at `K=16`. The empirical method should select `tau` using independent audit blocks and a confidence bound, not by looking at test labels.

### 8.3 Required Baselines

The toy should compare:

```text
uncalibrated score
global CP
group CP with irrelevant groups
reward-bin/rank-bin CP
Bonferroni alpha/K
selected-block calibration
CRC if applicable
CAP/FCR-style baseline if implementable
ACCS-v0
oracle tau
```

If reward-bin CP solves the toy completely, that is not failure. It means the next experiment must show why support, off-policy residuals, or moving budgets require a stronger RL-specific auditor.

Local hardened result:

```text
Reward-bin, rank-bin, and CRC-style baselines can repair the exact toy.
Therefore the toy should be used as the clean phenomenon figure, not as the
sole proof of ACCS method novelty. The method ceiling must come from the
RL-specific pieces: continuation-policy labels, support/no-overlap limits,
off-policy query laws, and audits of strong safe-RL proposers.
```

---

## 9. Theory Stack

The theory should be written as a stack, not as one overclaimed theorem.

### Theorem 1: Selection Amplification

There exists a finite action-selection problem where every candidate action has marginal failure probability below `alpha`, yet the selected action has false-certification risk `1-(1-p)^K`, approaching 1 as `K` grows.

Role in paper:

```text
Main phenomenon and Figure 1.
```

### Theorem 2: Residual-Cost Policy Specificity

For the same first action `(s,a)`, residual cost differs under different continuation policies:

```text
Z_H^{pi_cont}(s,a) != Z_H^{beta}(s,a)
```

Ordinary offline trajectories identify behavior-continuation outcomes, not necessarily deployment-continuation outcomes.

Role in paper:

```text
Explains why the certificate must declare a continuation policy or use simulator/OPE/model assumptions.
```

### Theorem 3: No-Overlap Impossibility

There exist two CMDPs that induce the same offline data distribution but have opposite residual safety outcomes after an unsupported queried action. Any non-abstaining certifier must falsely certify in one world.

Role in paper:

```text
Gives abstention a mathematical role and blocks fake "distribution-free safety" claims.
```

### Theorem 4: Finite-Rule Selective-Risk Control

For a finite prespecified rule family `H` and independent audit blocks, uniform concentration yields a high-probability guarantee:

```text
for selected h:
rho(h) <= alpha
```

provided:

```text
rho_UCB(h) <= alpha
yield_LCB(h) >= gamma
```

Role in paper:

```text
First positive theorem for ACCS-v0.
```

### Theorem 5: Weighted Off-Policy Extension

Under bounded or controlled density ratios between audit/query law and deployment/query law, weighted concentration controls:

```text
rho_Q(h) = E_P[wF] / E_P[wI]
```

Role in paper:

```text
RL-specific upgrade beyond generic selective conformal.
```

### Extension Theorem: Sequential Issued-Claim Risk

If time remains and the math works, extend from block-level population risk to a finite issued-claim stream using confidence sequences or filtration-conditional assumptions.

Role in paper:

```text
Optional oral booster, not required for the first complete paper.
```

---

## 10. Experiment Program

Experiments should not be a single linear path. They should be staged research bets.

### Phase 1: Exact Selection-Failure Toy

Goal:

```text
Show that marginal calibration can fail dramatically after action selection.
```

Artifacts:

```text
src/toy_selection_failure.py
outputs/toy_selection_failure.csv
figures/figure1_selection_amplification.pdf
```

Metrics:

```text
proposal marginal error
selected false certification
claim yield
selected reward
risk-yield-reward frontier
```

### Phase 2: ACCS-v0 vs Strong Statistical Baselines

Goal:

```text
Find out whether a selective-risk auditor adds value beyond simple reward-bin CP, Bonferroni, selected-block calibration, CRC, and CAP/FCR-style baselines.
```

This is where the method direction is chosen. If a generic baseline is strong, the paper can still pivot toward "RL-specific selective certification and evaluation" with that baseline included.

### Phase 3: Policy Mismatch and No-Overlap Toys

Goal:

```text
Show why offline safe RL makes the statistical problem harder than ordinary post-selection conformal prediction.
```

Panels:

```text
behavior continuation vs deployment continuation
unsupported high-reward actions
support-aware abstention
weighted/off-policy audit
```

### Phase 4: Strong Proposer Pilot

Goal:

```text
Demonstrate the phenomenon on at least one non-toy safe-RL proposer.
```

Candidate order:

```text
1. CAPSIQL checkpoint proposer on official DSRL CarCircle
2. CPQ direct OSRL checkpoint baseline
3. COptiDICE direct OSRL checkpoint baseline
4. SafeFQL pilot if code and environment costs are manageable
```

Current frozen main-table protocol:

```text
analysis/main_table_protocol.md
analysis/paper_assets/table_main_direct_osrl.csv
analysis/paper_assets/table_main_direct_osrl.md
```

Current evidence:

```text
CAPSIQL 50k q0.93, 3 seeds:
candidate false 0.0442, top selected false 0.0568,
ACCS risk 0.0228 at yield 0.8060.

CPQ 10k, three seeds:
q0.93 model_best is conservative with top selected false 0.0460;
q0.92 model_best has top selected false 0.0717,
ACCS risk 0.0225 at yield 0.8018.

COptiDICE 10k, three seeds:
q0.93 model_best has top selected false 0.0586,
ACCS risk 0.0220 at yield 0.8312;
q0.92 model_best has top selected false 0.0830,
ACCS risk 0.0217 at yield 0.7833.
```

### Phase 5: Benchmark-Scale Evidence

Goal:

```text
Move from interesting phenomenon to convincing top-conference paper.
```

Environment candidates:

```text
Hopper Safe-Velocity
Walker2d Safe-Velocity
HalfCheetah Safe-Velocity
Ant Safe-Velocity
PointGoal or CarGoal for visualization
```

Final tables must include:

```text
issued-claim risk with confidence intervals
target satisfied or not
claim yield
normalized reward
episode violation probability
fallback rate/reward/cost
```

---

## 11. Claim-Evidence Map

| Claim | Evidence needed | Current status |
|---|---|---|
| Calibration before selection is not calibration after selection. | exact toy, closed-form theorem, Figure 1 | local toy and server pilots supported; manuscript proof polish pending |
| Selected-claim false certification is a meaningful deployment metric. | formal estimand, toy, strong proposer audit | CAPSIQL, CPQ, and COptiDICE three-seed evidence now support the metric |
| Support-aware abstention is necessary, not just conservative. | no-overlap theorem and support stress test | local toy supported; DSRL support stress still pending |
| Residual safety claims are continuation-policy-specific. | policy mismatch theorem and two-step toy | local toy supported; simulator/model-based residual extension pending |
| ACCS-v0 can control selected-claim risk with useful yield. | finite-rule theorem and empirical risk-yield frontier | supported on synthetic, CAPS-style bridge, CAPSIQL, CPQ, and COptiDICE; reward-bin/CRC remain strong baselines |
| Strong safe-RL systems benefit from post-selection auditing. | CAPSIQL/CPQ/COptiDICE/SafeFQL pilots with common query bank | CAPSIQL, CPQ, and COptiDICE supported across three seeds under frozen main-table protocol; SafeFQL optional/pending |
| Action-level certificates affect episode safety. | horizon audit and episode violation metrics | pending |

No abstract or introduction should state a claim as achieved until this table has evidence.

---

## 12. Paper Narrative

### 12.1 Contribution List

Target contribution list after evidence exists:

1. **Problem.** We formalize selective safety certification for offline RL and distinguish proposal-level calibration from false certification among issued action claims.
2. **Phenomenon and limits.** We prove exact selection amplification and show that residual-cost certificates are policy-specific and impossible for unsupported actions without additional assumptions.
3. **Method.** We develop a support-aware selective auditor that controls issued-claim risk over prespecified certification rules while reporting yield, utility, and fallback behavior.
4. **Evaluation.** We audit toy systems and strong offline safe-RL proposers under common query banks, showing when ordinary calibration fails and when selective auditing repairs or diagnoses the failure.

### 12.2 Abstract Skeleton

Do not use as final abstract until experiments support it:

```text
Offline safe reinforcement learning systems increasingly choose deployment
actions by thresholding learned cost, reachability, or feasibility scores.
However, the action that receives a safety certificate is not a random proposal:
it is selected by budget filters, reward ranking, fallback logic, and repeated
deployment queries. We study selective safety certification, the problem of
controlling false safety claims among the actions that are actually certified
and executed. We first show an exact selection-amplification construction in
which proposal-level error is 4%, yet selecting the best of 16 apparently safe
actions raises false certification to 48%. We then show that residual safety
claims are continuation-policy-specific and that unsupported actions cannot be
certified from offline data without additional assumptions. To address this,
we develop a support-aware selective auditor that controls issued-claim risk
over prespecified certification rules while reporting yield, utility, and
fallback costs. Experiments on [TOY], [POLICY-MISMATCH], and [CAPS/SAFEFQL
TASKS] show that auditing selected action claims reveals failures hidden by
aggregate reward-cost metrics and by marginal calibration over proposals.
```

### 12.3 Introduction Flow

Paragraph 1: concede strength of existing safe RL.
Existing methods can learn cost-aware policies, feasible action sets, and budget-conditioned behavior. Do not create a straw man.

Paragraph 2: introduce the missing certificate object.
Deployment systems select actions from candidate banks. The selected action's certificate is a post-selection statistical claim.

Paragraph 3: show the counterintuitive failure.
A small marginal error rate can become large selected-claim false certification under reward ranking.

Paragraph 4: explain RL-specific difficulty.
Residual labels depend on continuation policy and support; ordinary offline logs do not automatically identify deployment residuals.

Paragraph 5: present the method family.
Support-aware selective auditing freezes query blocks, measures issued failures directly, and controls risk/yield tradeoffs.

Paragraph 6: preview evidence.
Exact toy, mismatch/no-overlap stress tests, and audit of strong proposers.

---

## 13. Visual Plan

### Figure 1: Calibration After Selection Failure

Left:

```text
K vs selected false certification
```

Right:

```text
risk-yield-reward frontier for global CP, group CP, Bonferroni,
selected-block baseline, ACCS-v0, oracle
```

### Figure 2: Deployment Query Block

Show:

```text
state -> candidate bank -> learned scores -> certificate issuer -> selected action/fallback
```

The figure must make clear that certification happens after candidate selection pressure is introduced.

### Figure 3: Support and Identifiability

Show two worlds with identical offline data but opposite unsupported residual cost.

### Figure 4: Strong-System Audit

For CAPS/SafeFQL:

```text
original system
original + global CP
original + selected audit
ACCS
```

Metrics on one compact risk-yield-utility plot.

---

## 14. What Not To Claim

Do not claim:

```text
first conformal offline safe RL method
valid for any unseen budget
individual-action safety without conditions
trajectory safety from one-step marginal coverage
pure offline residual certificate when labels come from simulator branching
CAPS is only policy-level
SafeFQL is irrelevant
group CP solves selection
ACCS controls FCR unless the theorem controls finite-stream FCR
```

Allowed high-ceiling claim:

```text
We study a deployment-specific certification problem that existing safe-RL
optimizers and marginal calibration procedures do not by themselves settle:
false safety claims among selected and executed actions.
```

---

## 15. Immediate Execution Plan

The next work should be ambitious but concrete.

### Step 1: Freeze the Research Object

Update `theory_proofs.md` to use:

```text
query block W
issuance I_h
failure F_h
rho(h)=E[F_h]/E[I_h]
yield(h)=E[I_h]
```

Keep FCR and sequential guarantees as extensions.

### Step 2: Implement Exact Toy

Create:

```text
src/toy_selection_failure.py
```

Required outputs:

```text
closed-form rho_K table
Monte Carlo validation
global/group/Bonferroni/selected-block/ACCS-v0 baselines
risk-yield-reward curve
```

### Step 3: Implement ACCS-v0

Create:

```text
src/selective_auditor.py
src/eval_metrics.py
```

ACCS-v0 should select over a finite rule family with independent audit data and confidence bounds.

### Step 4: Add Policy-Mismatch and No-Overlap Toys

Create:

```text
src/toy_policy_mismatch.py
src/toy_no_overlap.py
```

These tests decide whether the RL-specific story is genuinely stronger than generic selective conformal.

### Step 5: Only Then Start CAPS/SafeFQL Integration

Do not start heavy benchmark engineering until:

```text
selection amplification is visually strong
ACCS-v0 or a valid baseline controls selected risk
support/no-overlap story is clear
claim yield is nontrivial
```

This is not a downgrade. It is how to make the later big experiments meaningful.

---

## 16. When To Ask GPTPro Again

Do not ask for another broad opinion now. The next useful GPTPro review should happen after there is evidence:

```text
Figure 1 from exact toy
ACCS-v0 risk-yield-reward frontier
updated theory stack
policy mismatch/no-overlap toy
one strong proposer pilot if available
```

Then ask whether the evidence supports:

```text
problem paper
method paper
theory paper
systems audit paper
```

Until then, the right move is to build evidence and let the strongest path emerge.

---

## 17. Current Working Verdict

The idea is worth pursuing because the core object is real:

```text
selected action claims are not the same as proposal-level calibration.
```

The paper has high ceiling if it combines:

```text
exact counterexample
RL-specific impossibility
support-aware selective auditor
strong-system audit
risk-yield-utility evidence
```

The current experimental center is no longer a toy-only idea. CAPSIQL, CPQ, and
COptiDICE now run through the same official DSRL query-bank/auditor contract,
and the first direct-OSRL main-table protocol has been frozen in
`analysis/main_table_protocol.md`. The next high-upside push is to turn this
protocol into the paper's experiment section, add broader stress tests, and add
SafeFQL only if it can be made comparable.

The blueprint should therefore remain ambitious. The project is not being narrowed before results. It is being organized into several high-upside experiments that can reveal which version is strong enough for a top venue.
