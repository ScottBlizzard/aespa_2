# Theory Spine: Support-Aware Selective Safety Certification

> Last updated: 2026-06-30
> Role: theory plan for the AAAI_2 oral-ambition route
> Current status: local exact toys support the first phenomenon and three RL-specific stressors; the main theorem/proposition block plus fixed episode-audit corollary are now inserted in `aaai2027/paper.tex`; appendix-level proof polish remains pending.

---

## 0. Theory Thesis

The theory should support a high-ceiling claim, not a small conformal wrapper:

```text
A safety score is not a safety certificate.
Calibration before action selection is not calibration after action selection.
Offline safe-RL certification must account for selection, support, and the
declared continuation policy.
```

The paper's theory should therefore be organized around five claims:

1. **Selection amplification.** Marginally calibrated proposal-level scores can produce high false-certification risk among selected actions.
2. **Direct selective-risk control.** A finite-rule auditor can control issued-claim risk with finite audit data.
3. **Policy-specific residual labels.** Residual-cost certificates depend on the continuation policy after the first action.
4. **No-overlap impossibility.** Unsupported actions cannot receive nontrivial distribution-free certificates from offline data.
5. **Off-policy certification.** Deployment-query certification needs explicit density-ratio, support, or simulator-label assumptions.

This theory stack is intentionally more ambitious than a standard split-conformal proof. It turns the project into an RL-specific selective certification problem.

---

## 1. Statistical Unit: Deployment Query Block

The unit of analysis is not a single candidate action. It is the full deployment query block:

```text
W = (S, B, {A_j, R_j, C_j, O_j, Z_j}_{j=1}^K)
```

where:

- `S` is the state;
- `B` is the requested residual budget;
- `A_j` is candidate action `j`;
- `R_j` is a reward or utility score;
- `C_j` is a learned cost, feasibility, reachability, or conformal score;
- `O_j` is support or overlap evidence;
- `Z_j = Z_H^{pi_cont}(S,A_j)` is the residual cost after taking `A_j` and then following the declared continuation policy `pi_cont`.

A certification rule maps a block to either one issued action or abstention:

```text
h(W) in {1, ..., K, abstain}
```

Define:

```text
I_h(W) = 1{h(W) != abstain}
```

```text
F_h(W) = 1{h(W)=j and Z_j > B}
```

The main population estimand is:

```text
rho(h) = E[F_h(W)] / E[I_h(W)]
```

with the convention that rules with near-zero `E[I_h]` are not useful. The corresponding yield is:

```text
yield(h) = E[I_h(W)]
```

The main paper target should be:

```text
rho(h) <= alpha and yield(h) >= gamma
```

This is different from:

```text
P[Z_j <= U_j] >= 1 - alpha
```

which is proposal-level marginal coverage and does not by itself control selected-claim risk.

---

## 2. The Old Marginal-Coverage Inference Is Invalid

Suppose a conformal upper bound satisfies:

```text
P[Z <= U] >= 1 - alpha
```

and the system issues a claim when:

```text
U <= B
```

Marginal coverage implies only:

```text
P[{U <= B} and {Z > B}] <= P[Z > U] <= alpha
```

It does not imply:

```text
P[Z > B | U <= B] <= alpha
```

The best direct bound is:

```text
P[Z > B | U <= B] <= alpha / P[U <= B]
```

This denominator is the core problem. If issuance is rare or if failures concentrate among issued claims, the selected-claim risk can be much larger than `alpha`.

Paper consequence:

```text
Never claim selected-action safety from ordinary marginal conformal coverage.
```

---

## 3. Theorem 1: Selection Amplification

### Claim

There exists a one-state action-selection problem where every proposed action has failure probability below `alpha`, but the selected action has false-certification risk approaching one as the candidate set grows.

### Construction

For each query block, sample:

```text
X_1, ..., X_K iid Uniform[0,1]
```

Let:

```text
A_j = a(X_j)
R_j = X_j
Z_j = 1{X_j > 1 - p}
B = 0.5
```

Assume the learned safety score certifies every candidate, so the deployment system selects:

```text
h_global(W) = argmax_j R_j = argmax_j X_j
```

Each individual proposal has false-certification probability:

```text
P[Z_j > B] = p
```

For `p=0.04` and `alpha=0.05`, each proposal is marginally below the nominal error target.

### Statement

The selected-claim false-certification risk is:

```text
rho(h_global) = P[max_j X_j > 1 - p] = 1 - (1 - p)^K
```

Thus:

```text
rho(h_global) -> 1 as K -> infinity
```

even though every proposal has marginal false-certification probability `p < alpha`.

### Proof Sketch

The selected claim is false exactly when at least one of the `K` candidate actions lies in the failing region `(1-p, 1]`. Since the candidates are independent:

```text
P[no failure among K candidates] = (1 - p)^K
```

Taking the complement gives the result.

### Local Evidence

Implemented in:

```text
src/toy_selection_failure.py
src/toy_selection_failure_hardened.py
```

At `p=0.04` and `K=16`:

```text
1 - 0.96^16 = 0.4796...
```

Local Monte Carlo:

```text
global CP selected false certification = 0.478205
hardened rerun global selected false certification = 0.479055
```

### Paper Role

This is the first theorem and the first figure. It is the clean reason reviewers should care.

---

## 4. Corollary 1: Strong Simple Baselines Can Repair the Toy

### Claim

The selection-amplification toy is a phenomenon test, not proof that ACCS-v0 has unique algorithmic novelty.

### Statement

In the construction above, the failure event is monotone and directly aligned with the reward feature:

```text
F = 1{X > 1 - p}
```

Therefore a reward-threshold, reward-bin, rank-bin, or CRC-style threshold rule can learn to avoid the failing tail using independent audit labels.

### Local Evidence

At `K=16` in `outputs/toy_selection_failure_hardened.csv`:

| Method | Selected risk | Yield | Reward |
|---|---:|---:|---:|
| global CP | 0.479055 | 1.000000 | 0.941323 |
| reward-bin UCB, 20 bins | 0.000000 | 1.000000 | 0.891370 |
| rank-bin UCB | 0.024345 | 1.000000 | 0.823867 |
| CRC-style threshold auditor | 0.032165 | 1.000000 | 0.903426 |
| ACCS-v0 | 0.032165 | 1.000000 | 0.903426 |

### Paper Consequence

Do not sell the toy as a unique ACCS method win. Sell it as the cleanest demonstration that the estimand is wrong if we only check marginal proposal coverage. The method novelty must come from the RL-specific parts:

```text
continuation-policy residual labels
support/no-overlap abstention
off-policy query distributions
auditing strong safe-RL proposers
```

This result raises the paper's bar and prevents an avoidable reviewer rejection.

---

## 5. Theorem 2: Finite-Rule Selective-Risk Control

### Claim

Given independent audit query blocks and a prespecified finite family of certification rules, we can select a useful rule with high-probability control of issued-claim risk.

### Setup

Let:

```text
H = {h_1, ..., h_M}
```

be a finite rule family fixed before seeing audit outcomes. Let audit blocks:

```text
W_1, ..., W_n iid P
```

For each rule `h`, define:

```text
f_h = E[F_h(W)]
i_h = E[I_h(W)]
rho(h) = f_h / i_h
```

and estimates:

```text
fhat_h = (1/n) sum_i F_h(W_i)
ihat_h = (1/n) sum_i I_h(W_i)
```

Let:

```text
eps_n = sqrt(log(4M/delta) / (2n))
```

### Statement

With probability at least `1-delta`, for all `h in H`:

```text
f_h <= fhat_h + eps_n
i_h >= ihat_h - eps_n
```

Therefore any selected rule satisfying:

```text
ihat_h > eps_n
(fhat_h + eps_n) / (ihat_h - eps_n) <= alpha
ihat_h - eps_n >= gamma
```

also satisfies:

```text
rho(h) <= alpha
yield(h) >= gamma
```

on the audit/query law `P`.

### Proof Sketch

Apply Hoeffding's inequality to `F_h` and `I_h` for each `h`, then union bound over `M` rules and the two estimates. On the simultaneous good event, divide the upper bound for `f_h` by the lower bound for `i_h`.

### Implementation Mapping

Implemented in:

```text
src/selective_auditor.py
```

The local ACCS-v0 family uses threshold rules:

```text
h_tau(W): issue the highest-reward candidate with X_j <= tau
```

The same proof applies to larger prespecified rule families that include support, budget, rank, proposer identity, or fallback decisions.

### Elevation

This theorem is intentionally generic. It lets the paper turn any strong base safe-RL system into an auditable proposer:

```text
CAPS/SafeFQL/BCRL/AEGIS propose candidates.
ACCS audits selected-claim risk over a fixed query-bank protocol.
```

The theorem becomes top-conference-relevant only when paired with RL-specific labels and support assumptions, developed below.

---

## 6. Proposition 1: Residual-Cost Labels Are Continuation-Policy-Specific

### Claim

A residual-cost certificate is meaningless unless it declares the continuation policy under which residual cost is measured.

### Statement

For the same initial state-action pair `(s,a)`, two continuation policies can induce different residual costs:

```text
Z_H^{pi_1}(s,a) != Z_H^{pi_2}(s,a)
```

Therefore calibration labels from behavior-policy trajectories:

```text
Z_H^{beta}(s,a)
```

do not automatically calibrate deployment certificates for:

```text
Z_H^{pi_cont}(s,a)
```

unless additional assumptions or estimators connect `beta` to `pi_cont`.

### Proof Sketch

Construct a two-step CMDP. After the first action, the system reaches a state where policy `pi_1` takes a rescue action with zero cost and policy `pi_2` takes an exploit action with cost one. The first-step `(s,a)` is identical, but the residual horizon cost differs.

### Local Evidence

Implemented in:

```text
src/toy_policy_mismatch.py
```

At `K=16`:

```text
behavior-rescue labels risk = 0.000000
deployment-exploit accept-all risk = 0.814995
declared-policy support-aware cap risk = 0.000000
```

### Paper Role

This is one of the main RL-specific reasons the paper is not just generic selective conformal prediction.

---

## 7. Theorem 3: Episode-Budgeted Selective-Risk Control

### Claim

Action-level selective-risk control does not automatically imply
episode-level safety when many certificates are issued inside the same
trajectory. However, if certificate emission is explicitly budgeted per
episode, the same finite-rule audit logic can control an episode-level
false-certification target.

### Setup

Let an episode be a sequence of query blocks:

```text
E = (W_1, ..., W_T)
```

where `T` may be fixed or random. For a base certification rule `h` and
an emission budget `m`, define the capped rule `h^m`:

```text
h^m issues the first at most m certificates that h would issue in the episode.
```

In a logged proxy, "first" means the order of query blocks anchored to the
logged episode. In a closed-loop simulator audit, "first" means online time
order. For an episode `E`, define:

```text
J_{h,m}(E) = 1{h^m issues at least one certificate in E}
G_{h,m}(E) = 1{h^m issues at least one false certificate in E}
```

The episode-level selective risk and episode yield are:

```text
rho_ep(h,m) = E[G_{h,m}(E)] / E[J_{h,m}(E)]
yield_ep(h,m) = E[J_{h,m}(E)]
```

Block yield can be reported separately as:

```text
block_yield(h,m) = E[number of issued blocks] / E[number of query blocks]
```

### Statement

Let:

```text
A = H x M_budget
```

be a finite family of base rules and episode emission budgets fixed before
observing audit outcomes. Let audit episodes:

```text
E_1, ..., E_N iid P_ep
```

For each pair `a=(h,m)`, define:

```text
ghat_a = (1/N) sum_i G_a(E_i)
jhat_a = (1/N) sum_i J_a(E_i)
eps_N = sqrt(log(4|A|/delta) / (2N))
```

With probability at least `1-delta`, every selected pair satisfying:

```text
jhat_a > eps_N
(ghat_a + eps_N) / (jhat_a - eps_N) <= alpha_ep
jhat_a - eps_N >= gamma_ep
```

also satisfies:

```text
rho_ep(a) <= alpha_ep
yield_ep(a) >= gamma_ep
```

under the same episode query law.

### Proof Sketch

Apply Hoeffding's inequality to the bounded episode indicators
`G_a(E)` and `J_a(E)` for each finite pair `a`, then union bound over
`2|A|` empirical means. On the simultaneous good event:

```text
E[G_a] <= ghat_a + eps_N
E[J_a] >= jhat_a - eps_N
```

Dividing the numerator upper bound by the positive denominator lower bound
gives the episode selective-risk result. This is the same statistical spine
as Theorem 2, but the unit of exchangeability is now the episode rather than
the query block.

### Implementation Mapping

Implemented proxy scaffold:

```text
src/run_dsrl_episode_proxy_audit.py
scripts/summarize_episode_proxy_outputs.py
outputs/phase_dsrl_episode_capsweep_proxy_car_q92_summary.md
analysis/paper_assets/table_dsrl_episode_capsweep_proxy_car_q92.csv
```

The current experiment is a logged episode-block proxy, not a simulator
closed-loop guarantee. Its role is to test whether the risk-allocation path is
non-vacuous before spending server time on online rollouts.

### Paper Role

This theorem raises the ceiling without overclaiming:

```text
block ACCS = action-certificate reliability
episode-budgeted ACCS = formal route toward trajectory-certificate reliability
closed-loop simulator audit = next empirical validation target
```

The cap-sweep result gives the first positive evidence for this route: cap 4
keeps episode-proxy false certification below 3% on CPQ and COptiDICE while
issuing at least one certificate in every logged test episode.

### Corollary: Fixed-Rule Exact Episode Audit

The large finite family above is useful for adaptive rule selection, but it is
statistically expensive at the episode level. If the emitted-cap rule is fixed
before seeing audit labels, no union bound over thresholds is needed.

Let `a` be a pre-registered episode rule and let:

```text
K = sum_i G_a(E_i)
N = sum_i J_a(E_i)
```

be the number of false issued episodes among issued audit episodes. For
`N > 0`, define `U_CP(K,N,delta)` as the one-sided Clopper-Pearson upper bound:

```text
Pr_{p = U_CP}[ Binomial(N, p) <= K ] = delta
```

Then, under iid audit episodes:

```text
Pr( rho_ep(a) <= U_CP(K,N,delta) ) >= 1 - delta.
```

This is the right route for the current closed-loop CPQ diagnostic: the rule
"issue at most the first `m` policy-step certificates per episode" can be fixed
before audit labels. In the current 4090 three-seed 200/200 frontier, CPQ
cap512 has `K=12, N=600` on CarCircle test episodes, giving a one-sided 95%
exact upper bound of `0.0322`, and `K=0, N=600` on BallCircle test episodes,
giving `0.0050`. This cap saturates the full CarCircle and BallCircle episodes
at 300 and 200 issued certificates per episode, respectively. The matched
COptiDICE stress case has `K=365, N=600` on CarCircle and `K=533, N=600` on
BallCircle, with one-sided 95% exact upper bounds `0.6415` and `0.9089`.
DroneCircle is the boundary diagnostic: CPQ has `K=90, N=600` with upper bound
`0.1761`, while COptiDICE has `K=576, N=600` with upper bound `0.9723`.

This does not solve adaptive threshold selection. It gives a cleaner
trajectory-certificate route: pre-register a tiny emitted-cap family, audit it
at the episode level with exact binomial confidence, and keep larger adaptive
families as a later extension.

---

## 8. Theorem 4: No-Overlap Impossibility

### Claim

Unsupported actions cannot receive nontrivial distribution-free safety certificates from ordinary offline data.

### Setup

Let an offline behavior distribution only cover actions with:

```text
X <= x_support
```

and suppose deployment may query actions with:

```text
X > x_support
```

### Statement

There exist two CMDPs, `M0` and `M1`, such that:

1. `M0` and `M1` induce the same offline data distribution under the behavior policy.
2. For all supported actions, the transition and cost laws are identical.
3. For unsupported queried actions, `M0` assigns safe residual cost and `M1` assigns unsafe residual cost.

Any certifier that issues a safe certificate for unsupported actions with positive probability must have false-certification risk one on at least one of the two worlds conditional on those issued unsupported claims.

### Proof Sketch

Because the offline data distribution is identical under `M0` and `M1`, any data-dependent certifier has the same output distribution in both worlds. If it certifies an unsupported action as safe, choose the world where that unsupported action is unsafe. No distribution-free procedure can distinguish the two worlds from the observed data.

### Local Evidence

Implemented in:

```text
src/toy_no_overlap.py
```

At `K=16`:

```text
M0 safe unsupported / naive certify risk = 0.000000
M1 unsafe unsupported / naive certify risk = 0.814225
M1 support-aware cap risk = 0.000000
```

### Paper Role

This theorem gives abstention or support-aware capping a formal role. It is not a cosmetic conservative choice; it is required when the evidence object is unidentifiable.

---

## 9. Theorem 5: Weighted Off-Policy Selective Certification

### Claim

If audit query blocks are sampled from one law but deployment query blocks follow another, selected-claim risk requires explicit off-policy weighting or support checks.

### Setup

Let audit blocks follow law `P` and deployment query blocks follow law `Q`. Assume `Q` is absolutely continuous with respect to `P` and define:

```text
w(W) = dQ(W) / dP(W)
```

For a rule `h`, the deployment selective risk is:

```text
rho_Q(h) = E_Q[F_h(W)] / E_Q[I_h(W)]
         = E_P[w(W) F_h(W)] / E_P[w(W) I_h(W)]
```

where `I_h(W)` indicates that the rule issues a certificate and `F_h(W)`
indicates that the issued certificate is false. The denominator is random at
the empirical level, so the guarantee must upper-bound weighted false issuance
and lower-bound weighted issuance before taking their ratio.

### Statement

Assume:

```text
0 <= w(W) <= W_max
```

and let `H` be finite and fixed before the audit labels are observed. Given
`n` iid audit blocks from `P`, define the weighted empirical numerator and
denominator:

```text
Fhat_Q(h) = (1/n) sum_i w(W_i) F_h(W_i)
Ihat_Q(h) = (1/n) sum_i w(W_i) I_h(W_i)
```

For confidence level `delta`, use a uniform bounded Hoeffding radius:

```text
eps_w = W_max sqrt(log(4|H|/delta) / (2n)).
```

With probability at least `1-delta`, simultaneously for all `h in H`:

```text
E_Q[F_h] <= Fhat_Q(h) + eps_w
E_Q[I_h] >= Ihat_Q(h) - eps_w.
```

Therefore any selected rule satisfying:

```text
Ihat_Q(h) > eps_w
(Fhat_Q(h) + eps_w) / (Ihat_Q(h) - eps_w) <= alpha
```

has deployment selective risk `rho_Q(h) <= alpha` under law `Q`. A yield
constraint can be added by requiring `Ihat_Q(h) - eps_w >= gamma`.

The same accounting can use an empirical-Bernstein or effective-sample-size
radius when the weights are not too concentrated. A useful descriptive audit
quantity is:

```text
ESS_h = (sum_i w(W_i) I_h(W_i))^2 / sum_i (w(W_i) I_h(W_i))^2.
```

Small `ESS_h` is not a theorem failure; it is the price of certifying a shifted
deployment query law with limited audit support. If `Q` is not absolutely
continuous with respect to `P`, then some deployment blocks have no audit-law
support and no weighted offline guarantee is possible there. The certifier must
abstain, cap the support region, or introduce external simulator/model
assumptions.

### Proof Sketch

For each fixed `h`, both `w(W)F_h(W)` and `w(W)I_h(W)` lie in
`[0, W_max]`. Apply Hoeffding's inequality to both variables and union-bound
over numerator/denominator events and over `|H|` rules. On the resulting event,
the population deployment numerator is at most `Fhat_Q(h)+eps_w` and the
population deployment denominator is at least `Ihat_Q(h)-eps_w`. Taking the
ratio gives the displayed upper bound whenever the lower denominator is
positive. Because the event is uniform over `H`, the rule may be selected after
auditing using only these certified quantities.

### Paper Role

This is the cleanest route for raising the theory above generic post-selection conformal prediction. Offline safe RL is rarely on-policy at deployment; the certificate must state the query law, support condition, and residual-label source.

### Evidence Status

Implemented as a local diagnostic in `src/toy_offpolicy_shift.py`. The toy uses
audit law `P` uniform over a selected-query score `x` and deployment law
`Q_a` with density `a x^(a-1)`, so `w_a(x)=a x^(a-1)`. At shift `a=8`, the
unweighted audit has 33.90% deployment false certification at 41.19% yield,
while known-ratio weighting tracks the oracle at 4.45% risk and 28.49% yield.
A support cap gives 0% risk with 27.23% yield. This is appendix/theory-support
evidence, not a DSRL main result.

---

## 10. Optional Extension: Finite-Stream FCR

### Claim

Population selective risk and finite-stream false-coverage rate are related but not identical.

Population target:

```text
rho(h) = E[F_h] / E[I_h]
```

Finite-stream target:

```text
FCR_T = E[ sum_{t=1}^T F_t / max(1, sum_{t=1}^T I_t) ]
```

History-conditional target:

```text
P(F_t=1 | I_t=1, history) <= alpha
```

These are different estimands. The main paper should control only what the theorem actually proves. If a confidence-sequence or martingale extension is developed later, it can become an additional contribution.

---

## 11. Method Taxonomy After Hardened Baselines

The hardened toy changes the theory story in a useful way.

| Object | Status | Paper role |
|---|---|---|
| Global/marginal conformal | fails after selection | baseline expected to fail |
| Group/Mondrian CP | can still fail if groups miss the selection feature | baseline / primitive |
| Reward-bin / rank-bin | repairs the exact toy | strong local baseline |
| CRC-style threshold auditor | matches ACCS-v0 on the toy | strong statistical baseline |
| ACCS-v0 finite-rule auditor | controls toy risk | minimal positive auditor |
| Support-aware/off-policy auditor | local shift toy implemented | high-ceiling method direction |
| CAPS/SafeFQL audit | not yet implemented | decisive prior-work test |

The conclusion is not that ACCS is weak. The conclusion is that the final ACCS must be defined as an RL-specific selective auditor, not as a rebranded threshold on a one-dimensional toy.

---

## 11. Theory-to-Experiment Map

| Theory claim | Evidence | Status |
|---|---|---|
| selection amplification | exact toy and closed form `1-(1-p)^K` | local supported |
| global/group CP fail after selection | `toy_selection_failure.csv` and hardened output | local supported |
| simple statistical baselines can repair toy | reward-bin/rank-bin/CRC hardened output | local supported |
| finite-rule selective audit controls toy risk | `selective_auditor.py`, ACCS-v0 output | local supported; proof sketch present |
| residual labels are continuation-policy-specific | `toy_policy_mismatch.csv` | local supported |
| no overlap requires abstention/support control | `toy_no_overlap.csv` | local supported; proof sketch present |
| off-policy query law needs weighting/support | `toy_offpolicy_shift.csv` | local supported; theorem polish pending |
| strong safe-RL systems need selected-claim audit | CAPS/SafeFQL pilot | pending |
| action-level certificates imply trajectory safety | should not be claimed | not supported |

---

## 12. Claim-Evidence Constraints

Allowed now:

```text
Marginal proposal-level calibration can fail dramatically after deployment-time
action selection.
```

```text
The exact toy demonstrates the wrong estimand, not unique ACCS method novelty.
```

```text
Residual safety certificates must declare a continuation policy and support
condition.
```

Not allowed yet:

```text
ACCS beats all selective baselines.
```

```text
ACCS improves CAPS/SafeFQL selected-claim reliability.
```

```text
Action-level certification guarantees trajectory safety.
```

```text
Pure offline logs identify target-policy residual costs without overlap,
branching, OPE, or model assumptions.
```

---

## 13. Elevated Paper Position

The strongest paper position after the local results is:

> **We identify selected-action safety certification as a missing evidence object for offline safe RL. We prove that marginal calibration can fail after action selection, show that ordinary offline residual labels are policy-specific and unsupported actions are unidentifiable, and develop a finite-rule auditing framework that can be extended to support-aware and off-policy certification of strong safe-RL proposers.**

This position is more ambitious than the original ACCS wrapper. It points toward a paper about the statistical contract of deployed safe-RL systems.

---

## 14. Next Theory Work

1. Convert Theorem 2 into polished notation suitable for `aaai2027/paper.tex`.
2. Formalize the two-CMDP no-overlap construction with a diagram.
3. Decide whether the positive theorem should use Hoeffding, empirical Bernstein, or confidence sequences.
4. Convert Theorem 5 into publication-ready notation if the off-policy toy is promoted beyond appendix diagnostics.
5. Keep sequential FCR as an extension unless a clean martingale theorem emerges.
