I reviewed the requested files, index/manifest, theory, manuscript skeleton, and primary competitor papers. The repository is still a research-design scaffold: implementation modules are only planned, every experimental phase is pending, and the manuscript explicitly disclaims empirical claims.

## 1. Overall verdict

### Is the thesis genuinely stronger than “conformal prediction + offline safe RL”?

**Not in its current mathematical form.**

Right now ACCS is:

1. train a cost-to-go predictor;
2. apply group/Mondrian split conformal calibration;
3. threshold the conformal upper bound by a deployment budget;
4. select, replace, or abstain;
5. log the calibration group and sample count.

That is a reasonable system design, but scientifically it is still “conformal calibration on top of offline safe RL.” Provenance and abstention are useful engineering features, not enough by themselves to establish a new problem class.

It becomes genuinely stronger only if the paper owns the problem of **calibration after deployment-time action selection**:

> A learned feasibility score may be calibrated marginally before deployment, yet become badly miscalibrated among the actions actually selected, certified, and executed under adaptive budgets.

That is a sharper and harder problem than ordinary conformal wrapping.

### Is “safety is a claim, not a cost” defensible?

**As a slogan: partly. As a literal scientific thesis: no.**

A cost is a task quantity. A safety claim is an epistemic statement about that quantity. They are not competing concepts. Worse, AEGIS, BCRL, CAPS, robust shielding, and other methods do make explicit mathematical safety claims; saying the literature treats safety merely as a cost would be a straw man.

The defensible statement is:

> **A learned cost or feasibility estimate is not a calibrated deployment certificate.**

Or:

> **Empirical budget satisfaction is not evidence that a selected action was justified ex ante.**

That distinction is real, potentially important, and less grandiose.

### Realistic ceiling

**Current formalization: not viable.**

Three blockers are severe enough to cause rejection independently:

1. Proposition 2 does not prove the claimed accepted-action miscoverage guarantee.
2. The residual-cost calibration target is generally not observable from ordinary offline trajectories under the deployed continuation policy.
3. The literature review misses SafeFQL, which already combines offline safe RL, deployment-time safe action selection, conformal threshold calibration, and finite-sample probabilistic coverage. SafeFQL is absent from the current paper index and PDF manifest.   SafeFQL explicitly claims conformal calibration of a learned safety boundary for finite-data error. ([ar5iv][1])

**After a substantial redesign: strong-accept ceiling.** Oral-level is plausible only if the paper contributes a genuinely new selection-aware theorem, a nontrivial impossibility result about unsupported actions, and a full benchmark showing a large real-world calibration-after-selection failure that ACCS fixes with modest utility loss.

---

## 2. Novelty threat audit

### 1. SafeFQL is currently the most dangerous omission

SafeFQL learns a reachability-style safety value, uses it for safe action selection, and then applies conformal calibration to adjust the learned safety boundary under finite data. Its calibration is for a fixed policy and state-level safety set rather than your proposed cumulative-budget, selected-action protocol, so it does not completely subsume the best possible ACCS. But it destroys every broad formulation of:

* first conformal method for offline safe RL;
* first finite-sample calibration of offline safety estimates;
* first deployment-time safe-action method with conformal guarantees;
* first uncertainty-aware safety boundary for offline RL.

The surviving gap is much narrower:

> SafeFQL calibrates a fixed learned safety level set; ACCS must control false certification among adaptively selected action proposals and budget queries, across arbitrary base safe-RL scores.

Without that distinction, SafeFQL makes ACCS look late and incremental. ([ar5iv][1])

### 2. Robust Probabilistic Shielding threatens the “statistical action certificate” claim

Robust Probabilistic Shielding constructs an action-level shield from offline data using an interval MDP. It defines a safe-action set and proves, with high probability over the dataset, that actions allowed by the shield are safe in the true MDP. ([arXiv][2])

Its assumptions are restrictive: known safe/unsafe states, knowledge of the MDP transition graph, discrete action structure, and a reach-avoid specification. ([arXiv][2]) That leaves room for a high-dimensional, model-agnostic, cumulative-budget method. But ACCS cannot claim to introduce statistical action-level safety certification from offline data.

### 3. AEGIS and BCRL largely kill the action-set and budget-uniform story

AEGIS defines a feasibility (Q)-function whose threshold directly identifies viable actions for each state-budget pair. Its theory characterizes a common feasible policy over all feasible budgets and reduces infinite-horizon viability to a one-step action condition. ([开放评论][3])

BCRL explicitly defines

[
\mathcal A_P(s,\delta)={a:Q_C^*(s,a)\leq\delta}
]

and proves that policies restricted to its budget-conditioned persistent safe sets satisfy the cumulative cost constraint. It also tracks dynamic budgets in stochastic environments. ([arXiv][4])

Therefore:

**Yes, AEGIS/BCRL make “one learned surface, thresholded at any requested budget” redundant.**

The only nonredundant meaning of “budget-uniform certificate” would be:

> simultaneous finite-sample control of false certification across budget-conditioned deployment distributions, including selection and support failure.

That is not what the current theory proves.

### 4. CAPS covers more of the paper’s motivating story than the current framing admits

CAPS is not merely policy-level. At each state it:

* gathers candidate actions from multiple policies;
* filters them using cost (Q)-values and accumulated cost;
* selects the highest-reward feasible action;
* uses a cost-minimizing fallback if the feasible set is empty. ([AAAI Publications][5])

Its safety analysis assumes a perfectly estimated optimal-cost (Q)-function and additional optimal-cost-variation conditions. ([AAAI Publications][6]) That is exactly where an auditor could help.

So CAPS does **not** kill a finite-data calibration contribution. It does kill claims that existing work:

* cannot operate at the action level;
* cannot adapt to moving budgets;
* cannot filter candidate actions at deployment;
* cannot use residual accumulated cost.

The correct positioning is:

> CAPS performs action filtering using learned cost estimates; ACCS audits whether the resulting selected actions support calibrated finite-data claims.

**CAPS+ACCS is necessary**, but it is only persuasive if compared against CAPS+global conformal and CAPS+selection-aware alternatives.

### 5. Conformal safety shielding makes a generic “conformal shield” incremental

Conformal Safety Shielding constructs action restrictions from conformal state-estimation sets and proves local and finite-horizon safety properties. ([arXiv][7])

The earlier Conformal Predictive Safety Filter applies conformal trajectory prediction to an RL controller and produces a runtime filter with probabilistic horizon-level collision guarantees under its assumptions. ([arXiv][8])

These methods differ substantially from offline cumulative-cost RL, but they establish that:

> conformal uncertainty + runtime action filtering + probabilistic safety

is already an established template.

ACCS survives only through the combination of:

* offline learned cost/feasibility scores;
* cumulative moving budgets;
* post-selection risk control;
* explicit support failure;
* base-policy-agnostic auditing.

### 6. TREBI eliminates novelty in real-time budget adaptation

TREBI already addresses offline safe RL under dynamically determined deployment-time budgets and claims trajectory-level constraint handling. ([arXiv][9])

It does not provide ACCS-style statistical action auditing, but it means “moving constraints without retraining” is background, not contribution.

### Exact claim wording that should be forbidden

| Forbidden wording                                                          | Defensible replacement                                                                                                                                            |
| -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| “The first action-level safety certificates for offline safe RL.”          | “A selection-aware audit protocol for learned action-feasibility scores.”                                                                                         |
| “Existing offline safe RL methods do not identify which actions are safe.” | “Existing methods identify feasible actions using learned or modeled scores, but generally do not calibrate false certification after deployment-time selection.” |
| “ACCS statistically justifies each individual action.”                     | “ACCS issues reports on individual proposals with validity defined over a declared proposal distribution or calibration group.”                                   |
| “Accepted actions violate the budget with probability at most (\alpha).”   | Forbidden until selective-risk—not marginal-coverage—is proved.                                                                                                   |
| “Action-conditional coverage.”                                             | Use “group-conditional marginal coverage” unless actions are genuinely discrete conditioning groups.                                                              |
| “Valid for any unseen budget.”                                             | “Simultaneously evaluated over a prespecified budget range under stated distributional assumptions.”                                                              |
| “Distribution-free deployment safety.”                                     | “Finite-sample risk control under exchangeability, policy-match, and support assumptions.”                                                                        |
| “Global conformal is invalid for action claims.”                           | “Global conformal may hide subgroup error and may be inefficient under heterogeneous residual distributions.”                                                     |
| “Abstention guarantees safety.”                                            | “Abstention transfers control to a separately specified fallback whose safety and utility are evaluated.”                                                         |
| “Provenance makes an action safe.”                                         | “Provenance records the assumptions and evidence supporting the statistical claim.”                                                                               |
| “Action-level guarantees imply trajectory safety.”                         | Keep the current explicit prohibition.                                                                                                                            |
| “CAPS is policy-level whereas ACCS is action-level.”                       | This is factually wrong.                                                                                                                                          |

---

## 3. Strongest possible reframing

### Recommended thesis

> Existing budget-adaptive offline safe-RL methods select actions by thresholding learned cost or feasibility scores. Under finite offline data, those scores can be miscalibrated, and selecting among candidate actions or across budgets can concentrate errors precisely among the actions that are executed. ACCS is a post-hoc, selection-aware auditor that controls false certification among issued action claims for a declared proposal and continuation policy, while abstaining when overlap or calibration support is inadequate.

This does four useful things:

1. It acknowledges that CAPS, AEGIS, and BCRL already produce action-level feasible sets.
2. It makes finite-data score error the problem.
3. It identifies action selection—not merely conformalization—as the technical obstacle.
4. It gives abstention a formal role through support impossibility rather than presentation-layer provenance.

### Title

Neither proposed title is ideal.

**“Safety Is a Claim, Not a Cost”** is memorable but risks sounding philosophical and technically imprecise.

**“Which Actions Are Safe Enough?”** sounds as though you will provide pointwise conditional safety probabilities, which the current method cannot do.

My recommendation:

> **Calibration After Action Selection: Safety Claims for Offline RL under Moving Budgets**

A more provocative alternative is:

> **A Cost Constraint Is Not a Certificate: Calibration After Action Selection in Offline RL**

Use “Safety is a claim, not a cost” as an opening sentence or section heading, not as the primary scientific title.

### What Figure 1 should show

Figure 1 should expose the statistical failure, not merely draw a wrapper pipeline.

**Panel A — Existing mechanism.** At one state, CAPS/BCRL/AEGIS proposes several actions with learned cost estimates under budget (b). Multiple actions appear feasible.

**Panel B — Calibration-after-selection failure.** Show that a naïve conformal bound has 95% marginal coverage over all proposals, but after selecting the highest-reward action among the apparently certified candidates, false certification rises to, for example, 20–30%. This must eventually be an actual result, not a cartoon.

**Panel C — ACCS behavior.** Show the risk–coverage frontier:

* supported action: certificate issued;
* unsupported action: abstain/fallback;
* false-certification rate near the target;
* utility retained relative to the unwrapped policy.

A small inset can show the report/provenance fields: target continuation policy, calibration population, group, effective sample size, risk level, budget range, and fallback. Do not make the metadata card the central visual.

---

## 4. Theory check

### The current Proposition 2 is not valid in the sense the paper needs

The theory currently proves group-marginal conformal coverage,

[
\Pr(Z\leq U\mid G=g)\geq 1-\alpha,
]

and then claims that accepting when (U\leq b) implies budget-violation risk at most (\alpha) for accepted actions.

Let (A={U\leq b}). The proof establishes only

[
\Pr(A\cap{Z>b}\mid G=g)
\leq
\Pr(Z>U\mid G=g)
\leq \alpha.
]

What deployment requires is

[
\Pr(Z>b\mid A,G=g)\leq\alpha.
]

Instead, the available bound is

[
\Pr(Z>b\mid A,G=g)
\leq
\frac{\alpha}{\Pr(A\mid G=g)}.
]

If the method issues claims for 10% of queries and all of the 5% marginal errors occur within that selected 10%, then overall conformal coverage is 95%, while accepted-claim miscoverage is 50%.

This is not a technicality. It invalidates the intended interpretation of the proposed “claim miscoverage” metric and the central certificate statement.

Post-selection conformal inference is a distinct problem because selection can break the required exchangeability or concentrate coverage failures. Existing work develops separate selection-conditional and false-coverage-rate controls for exactly this reason. ([arXiv][10])

### Proposition-by-proposition assessment

| Current result                                            | Assessment                                                                                                                                                                                                      |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Proposition 1: group-conditional conformal coverage       | Correct as a standard lemma, assuming genuinely exchangeable calibration and deployment queries. Not novel.                                                                                                     |
| Proposition 2: accepted-action risk control               | Incorrect for conditional miscoverage among accepted claims. This is the fatal issue.                                                                                                                           |
| Proposition 3: budget monotonicity                        | A one-line set-inclusion fact. Useful implementation property, not a theorem contribution.                                                                                                                      |
| Proposition 4: granularity trade-off                      | A reasonable heuristic and ablation hypothesis, not a mathematical proposition.                                                                                                                                 |
| Proposition 5: horizon union bound                        | Elementary and potentially confused because (Z_H) is already defined as a residual-horizon quantity.                                                                                                            |
| Proposition 6: aggregate safety does not identify support | Intuitively true but currently close to tautological.                                                                                                                                                           |
| Proposition 7: global calibration is insufficient         | Overstated. Global conformal can be perfectly marginally valid. It does not provide subgroup control or provenance, and may be inefficient, but conditioning is not universally required for marginal validity. |

The current theory itself classifies most of these claims as pending and acknowledges the horizon/distribution-shift boundary.

### The deployability-gap result is currently too obvious

“Two policies can have identical aggregate episode cost but different action-level support” is not sufficient for an oral-level negative theorem.

Make it an **observational indistinguishability result**:

> If a deployment state-action region has zero or insufficient probability under the offline calibration distribution, there exist two CMDPs that induce exactly the same offline data distribution and aggregate evaluation statistics but assign opposite residual-cost outcomes to the unsupported deployment action. Consequently, any distribution-free certifier that issues a nontrivial claim there must fail in one world; a valid certifier must abstain.

That result would:

* formally justify abstention;
* give provenance/support mathematical meaning;
* establish a fundamental limitation rather than a metric mismatch;
* connect directly to offline-RL coverage.

### The global-vs-action calibration argument

It is defensible only in a narrower form:

* global conformal provides marginal coverage over the pooled query distribution;
* it may under-cover some groups and over-cover others;
* Mondrian/group calibration can provide group-marginal guarantees when groups are prespecified and sufficiently supported;
* finer grouping is not universally more efficient;
* exact pointwise conditional coverage is generally impossible distribution-free without additional assumptions. ([arXiv][11])

For continuous actions, a cluster-level guarantee is not an action-conditional guarantee. The paper should say:

> action-specific report, group-marginal validity.

### A second fatal theory issue: the residual-cost target is policy-specific

The target should be written explicitly as

[
Z_H^{\pi_{\mathrm{cont}}}(s,a),
]

because it depends on what policy is followed after executing (a).

If calibration trajectories were generated by behavior policy (\beta), they reveal (Z_H^\beta), not the residual cost under:

* the ACCS shield;
* a CAPS switching policy;
* a cost-minimizing fallback;
* a newly selected replacement action;
* any other deployment continuation.

Ordinary split conformal does not repair this counterfactual policy mismatch. Off-policy conformal work requires explicit policy-shift machinery because this is a real identification problem. ([arXiv][12])

Before coding, the project must choose one of the following:

1. Calibration data genuinely generated under the exact continuation policy.
2. A valid off-policy conformal/OPE construction with overlap assumptions.
3. A model-based target with explicit model-error guarantees.
4. A weaker one-step safety target rather than residual-horizon cost.

Otherwise the certificate is calibrated for the wrong random variable.

### The theorem that would most increase perceived depth

The strongest target is a **selective, budget-uniform false-certification theorem**.

Define

[
R_g(b)
======

\Pr!\left(
Z_H^{\pi_{\mathrm{cont}}}>b
\mid
\text{certificate issued},,G=g
\right).
]

The desired theorem should say that, with probability at least (1-\delta) over the calibration sample,

[
\sup_{g\in\mathcal G}\sup_{b\in\mathcal B}R_g(b)\leq\alpha,
]

under clearly stated assumptions concerning:

* proposal distribution;
* continuation policy;
* overlap;
* group construction;
* candidate-action selection;
* minimum claim yield;
* trajectory dependence.

For sequential deployment, an even stronger version would control the false certification proportion among all issued claims over time, under predictable budget queries.

This would be meaningfully different from ordinary conformal prediction. Conformal risk control already shows how to control general monotone risks, so simply invoking it is not enough; the new part must address action selection, adaptive budgets, or Markov/off-policy dependence. ([arXiv][13])

A complementary impossibility theorem should prove that positive claim yield is impossible without overlap. Together, those two results could support oral-level theory.

---

## 5. Experimental bar

### Experiments absolutely required

#### A. A falsification-first exact toy environment

Before Safety Gym, construct a finite MDP where the exact residual-cost distribution is known.

The experiment must demonstrate:

* ordinary split conformal has nominal marginal coverage;
* selecting the highest-reward “certified” action produces severe accepted-set miscoverage;
* selection-aware ACCS restores the target error rate;
* error increases with candidate-set size (K);
* unsupported regions force abstention;
* global, group, and selection-aware calibration can be compared without estimator noise.

If this phenomenon does not appear clearly in the oracle toy setting, stop. There is no reason to spend benchmark compute.

#### B. Policy-specific calibration validation

Use simulator branching for evaluation:

1. sample a state-action query;
2. restore the simulator to that state;
3. take the proposed action;
4. run many continuations under the exact declared fallback/execution policy;
5. estimate the true residual-budget violation probability.

One realized rollout per action is not sufficient to validate action claims. It confounds stochastic luck, trajectory dependence, and calibration.

#### C. Direct competitor matrix

At minimum:

* CAPS;
* CAPS + global split conformal;
* CAPS + Mondrian/group conformal;
* CAPS + a standard conformal-risk-control or selective-conformal baseline;
* CAPS + ACCS;
* BCRL;
* AEGIS, subject to reproducibility;
* SafeFQL;
* SafeFQL with its original calibration;
* RPS in a compatible discrete/tabular experiment.

**CAPS+ACCS is necessary but not sufficient.** The strongest isolation is:

[
\text{CAPS}
\rightarrow
\text{CAPS+global CP}
\rightarrow
\text{CAPS+group CP}
\rightarrow
\text{CAPS+selection-aware ACCS}.
]

That identifies whether the contribution is grouping, conformalization, or actual selection correction.

#### D. Full-scale benchmark

For oral credibility, use the full or nearly full DSRL task family spanning Safety-Gymnasium, Bullet-Safety-Gym, and MetaDrive, rather than a few handpicked Safety-Gym tasks. CAPS itself evaluated 38 DSRL tasks, so a substantially narrower benchmark will look evasive. ([AAAI Publications][6])

Evaluate:

* multiple dataset qualities;
* interpolation and extrapolation budgets;
* at least five seeds;
* calibration-set-size sweeps;
* candidate-set-size sweeps;
* strict trajectory-level train/calibration/test separation;
* frozen grouping and hyperparameters before test;
* paired confidence intervals across tasks and seeds.

#### E. Shift and support stress tests

Include independent axes:

* behavior-policy shift;
* deployment budget shift;
* dynamics shift;
* cost-function shift;
* candidate-action distribution shift;
* rare-action support;
* horizon length.

The desirable behavior is not “coverage remains perfect under arbitrary shift.” It is:

> false-certification error remains controlled in support, while claim yield falls and abstention rises before validity collapses out of support.

#### F. Fallback and horizon evaluation

“Abstain” is not an executable RL action. The paper must specify whether abstention means:

* use a fixed safe policy;
* choose the minimum-cost candidate;
* terminate;
* request human intervention;
* hold the previous control.

Report the fallback’s reward and safety. If the fallback itself lacks a guarantee, abstention is merely uncertainty routing.

### Essential metrics

| Metric                                                 | Verdict                                                                                                                                    |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **False certification rate among issued claims**       | Primary. This is the real version of claim miscoverage.                                                                                    |
| **Claim yield / coverage**                             | Primary, but only on a fixed proposal stream or common query bank.                                                                         |
| **Risk–coverage curve**                                | Primary. More informative than one yield number.                                                                                           |
| **Utility at controlled false-certification risk**     | Primary end-to-end metric.                                                                                                                 |
| **Episode budget violation rate and magnitude**        | Primary; needed to show operational consequence.                                                                                           |
| **Abstention/fallback rate, reward, and cost**         | Primary.                                                                                                                                   |
| **Worst-group false certification**                    | Primary if group claims remain central.                                                                                                    |
| **Horizon risk / time to first violation / CVaR cost** | Important.                                                                                                                                 |
| **Certified utility area**                             | Secondary. Valid only with a prespecified budget measure and common proposal distribution.                                                 |
| **Unsupported safety success**                         | Do not use as a headline metric. It is partly circular because methods without certificates are classified as unsupported by construction. |

Replace “unsupported safety success” with:

> **aggregate-pass / external-audit-fail rate**

and apply the same frozen external auditor or simulator-ground-truth criterion to every method.

Do not define a “deployability gap” by subtracting aggregate budget success from claim yield. Those quantities have different denominators and meanings. Use a contingency table or a two-dimensional risk–coverage plot.

### Result pattern that would be compelling

An oral-shaped result would look roughly like this:

* strong unwrapped methods satisfy average episode budgets;
* naïve cost-score thresholding or ordinary conformal calibration has 15–30% false certification after selecting among candidate actions at nominal (\alpha=0.05);
* ACCS keeps false certification near 5% across budgets and candidate sizes;
* it retains at least 70–90% claim yield in supported regions;
* reward loss is under roughly 5–10% on in-support tasks;
* under shift, abstention rises sharply before false certification rises;
* wrapping CAPS, BCRL, or AEGIS gives consistent improvements rather than only helping a weak in-house policy;
* the benefit persists at the episode level, not only in an abstract calibration metric.

### Result pattern that kills the paper

Stop or radically reframe if:

* global or ordinary group conformal already achieves the same accepted-set risk;
* ACCS meets the target only by abstaining on more than half the proposals;
* utility drops by 15–20% or more in ordinary in-support settings;
* SafeFQL’s original calibration matches ACCS;
* gains disappear after common candidate streams and fixed hyperparameters are used;
* groups are handpicked from test residuals;
* calibration works only with simulator-generated target-policy rollouts unavailable in the claimed offline setting;
* action-level calibration improves but episode violations do not;
* the effect appears only in a constructed toy environment.

---

## 6. Reviewer attack simulation

| Likely rejection argument                                                                      | Does the current plan answer it?                                                                                                    | Exact fix                                                                                                                                                |
| ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. “SafeFQL already combines conformal calibration and offline safe RL.”**                   | **No.** SafeFQL is absent from the index.                                                                                           | Add it immediately. Reframe around post-selection false certification, cumulative moving budgets, and base-score auditing. Include a direct comparison.  |
| **2. “CAPS, AEGIS, BCRL, and RPS already identify safe actions.”**                             | **Partially.** The threat map names several works, but the thesis still overstates their policy-level nature.                       | Explicitly concede action-feasibility sets as prior work. Claim novelty only in calibrated finite-data auditing after selection.                         |
| **3. “The accepted-action theorem is mathematically wrong.”**                                  | **No.** Proposition 2 confuses joint marginal error with conditional error among accepted claims.                                   | Replace the method with selection-aware calibration or conformal risk control targeted directly at false certification among issued claims.              |
| **4. “Your residual-cost labels are generated under the wrong policy.”**                       | **No.** The documents mention a fixed continuation/fallback but do not establish how its counterfactual return is observed offline. | Define the target policy exactly and use valid off-policy calibration, target-policy calibration trajectories, or a weaker observable target.            |
| **5. “You promise individual-action validity but prove only group-marginal validity.”**        | **Partially.** The theory states group exchangeability, but the rhetoric says individual actions are statistically justified.       | Change the language to action-specific reports with group-/distribution-level validity. Add a conditional-coverage limitation theorem.                   |
| **6. “Budget uniformity is just threshold nesting.”**                                          | **No.** Proposition 3 is deterministic set monotonicity.                                                                            | Prove uniform selective-risk control over budget-conditioned query distributions, including changing state visitation and candidate selection.           |
| **7. “Provenance and abstention are product features, not ML contributions.”**                 | **Partially.** The plan reports them but does not make them mathematically necessary.                                               | Add a no-overlap impossibility theorem; formalize fallback utility and safety; treat the report schema as artifact support rather than headline novelty. |
| **8. “The experiment and metrics are circular and weaker than the competitors’ evaluations.”** | **No.** All phases are pending, and “unsupported safety success” privileges the proposed certifier by definition.                   | Use common query banks, simulator-ground-truth residual risk, full DSRL, selection-aware baselines, SafeFQL, and end-to-end fallback metrics.            |

The current adversarial review correctly recognizes the lack of evidence and several horizon/shift risks, but it does not identify the accepted-set conditioning error or the policy-specific target-identification problem.

---

## 7. Final action plan

### Must do before coding

1. **Freeze the statistical estimand.** Write the target as
   [
   Z_H^{\pi_{\mathrm{cont}}}(s,a)
   ]
   and specify the proposal policy, continuation policy, fallback, residual-budget update, horizon, and source of valid calibration labels.

2. **Delete or rewrite Proposition 2.** Add the accepted-set counterexample to the theory document. Do not implement the planned conformal module under the assumption that marginal coverage controls accepted-claim miscoverage.

3. **Choose the actual validity target.** It should be false-certification risk among issued claims, not ordinary prediction-interval coverage.

4. **Simplify the first method version.** Certify one already-proposed action or abstain to a fixed fallback. Treat selecting among multiple replacement actions as a separate extension requiring multiplicity or post-selection correction.

5. **Replace “action-conditional” with precise terminology.** State whether validity is global marginal, group marginal, selection conditional, or false-coverage-rate control.

6. **Rewrite the thesis and title.** Make calibration after action selection the paper’s problem. Move provenance to a supporting contribution.

7. **Update the literature gate.** Add SafeFQL, selective conformal/FCR work, conditional-coverage impossibility, and off-policy conformal prediction. Rewrite the threat map before implementation.

8. **Define a go/no-go oracle toy.** Required comparisons: uncalibrated score, global CP, group CP, conformal risk control, and selection-aware ACCS. Vary (K), budget, support, and horizon.

### Must do before the main benchmark

1. Prove a valid selective-risk theorem or state honestly that the method is heuristic.
2. Prove the no-overlap abstention result.
3. Validate policy-specific residual-cost labels independently.
4. Implement the full CAPS ablation chain.
5. Add SafeFQL and at least one AEGIS/BCRL comparison.
6. Use common proposal streams so claim yield cannot be gamed by changing the policy.
7. Use simulator branching for ground-truth residual-risk evaluation.
8. Freeze budget grids, groups, (\alpha), calibration sizes, and fallback before test evaluation.
9. Run full or near-full DSRL only after the exact toy confirms a substantial selection-induced calibration gap.
10. Report false certification, risk–coverage, utility, episode violation, fallback, and support jointly.

### Nice-to-have oral polish

1. A time-uniform theorem for adaptive sequential budget requests.
2. A bound quantifying degradation under estimated density ratios or bounded policy shift.
3. An optimality or lower-bound result for claim yield under support constraints.
4. One real-world or high-fidelity control case study.
5. A public machine-readable certificate schema containing target policy, calibration population, group, effective sample size, validity mode, risk level, and fallback.
6. A first figure built from actual post-selection miscalibration data rather than a conceptual cartoon.

**Do not launch Safety-Gym or DSRL server jobs yet.** The next artifact should be a small exact counterexample demonstrating that naïve conformal calibration fails after action selection, followed by a method that provably fixes that failure. Otherwise the compute will only produce polished evidence for a claim the present theory does not establish.

[1]: https://ar5iv.org/pdf/2603.15136 "https://ar5iv.org/pdf/2603.15136"
[2]: https://arxiv.org/pdf/2605.10293 "https://arxiv.org/pdf/2605.10293"
[3]: https://openreview.net/pdf?id=jLgGlHj30G "https://openreview.net/pdf?id=jLgGlHj30G"
[4]: https://arxiv.org/pdf/2603.22292 "https://arxiv.org/pdf/2603.22292"
[5]: https://ojs.aaai.org/index.php/AAAI/article/view/33726 "https://ojs.aaai.org/index.php/AAAI/article/view/33726"
[6]: https://ojs.aaai.org/index.php/AAAI/article/view/33726/35881 "https://ojs.aaai.org/index.php/AAAI/article/view/33726/35881"
[7]: https://arxiv.org/pdf/2506.17275v1 "https://arxiv.org/pdf/2506.17275v1"
[8]: https://arxiv.org/pdf/2306.02551 "https://arxiv.org/pdf/2306.02551"
[9]: https://arxiv.org/pdf/2306.00603 "https://arxiv.org/pdf/2306.00603"
[10]: https://arxiv.org/abs/2403.07728 "https://arxiv.org/abs/2403.07728"
[11]: https://arxiv.org/abs/1903.04684 "https://arxiv.org/abs/1903.04684"
[12]: https://arxiv.org/abs/2304.02574 "https://arxiv.org/abs/2304.02574"
[13]: https://arxiv.org/abs/2208.02814 "https://arxiv.org/abs/2208.02814"
