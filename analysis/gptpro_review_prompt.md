# GPTPro Review Package

> Last updated: 2026-06-23  
> Purpose: external high-reasoning review prompt for AAAI_2 after the oral upgrade.

## Files To Provide

Minimum package:

```text
D:\AAAI_2\idea_blueprint.md
D:\AAAI_2\analysis\oral_upgrade_plan.md
D:\AAAI_2\papers\literature_review.md
D:\AAAI_2\analysis\literature_threat_map.md
D:\AAAI_2\theory_proofs.md
D:\AAAI_2\analysis\claim_evidence_map.md
D:\AAAI_2\NEXT_STEPS.md
```

If GPTPro can read more context, also provide:

```text
D:\AAAI_2\papers\paper_index.csv
D:\AAAI_2\papers\code_reuse.md
D:\AAAI_2\aaai2027\paper.tex
D:\AAAI_2\analysis\adversarial_review.md
```

Optional PDFs if the interface supports attachments:

```text
D:\AAAI_2\papers\pdfs\2025_AAAI_CAPS_constraint_adaptive_policy_switching.pdf
D:\AAAI_2\papers\pdfs\2026_ICLRsub_AEGIS_almost_surely_safe_offline_rl.pdf
D:\AAAI_2\papers\pdfs\2026_ICAPS_BCRL_budget_conditioned_reachability.pdf
D:\AAAI_2\papers\pdfs\2026_arXiv_robust_probabilistic_shielding_osrl.pdf
D:\AAAI_2\papers\pdfs\2025_arXiv_conformal_safety_shielding.pdf
```

## Prompt

```text
You are acting as a brutally critical senior ML/RL program committee reviewer and area chair for an AAAI/ICLR-level paper. I want to push this project toward an oral-level submission, not merely an acceptable paper.

Please read the attached project files carefully. The current upgraded thesis is:

"Safety is a claim, not a cost. Offline safe RL methods can optimize or switch policies across budgets, but they generally do not say which individual deployment-time actions are statistically justified under the requested safety constraint. ACCS is a budget-uniform action certificate protocol that issues calibrated action-level safety claims with provenance, or abstains when evidence is insufficient."

The main direct competitors/threats are CAPS, AEGIS, BCRL, TREBI, Robust Probabilistic Shielding, and conformal safety shielding. I do not want a generic literature summary. I want you to attack whether this upgraded paper can survive as a high-ceiling/oral-ambition contribution.

Please answer in the following structure:

1. Overall verdict:
   - Is the upgraded thesis genuinely stronger than "conformal prediction + offline safe RL"?
   - Is "safety is a claim, not a cost" a defensible and nontrivial paper identity?
   - What is the realistic ceiling: weak accept, strong accept, oral-level, or not viable?

2. Novelty threat audit:
   - Which existing work most directly kills or weakens the claim?
   - Does CAPS already cover too much of the story?
   - Does AEGIS/BCRL make the budget-uniform certificate angle redundant?
   - Does conformal safety shielding make ACCS look incremental?
   - What exact claim wording should be forbidden?

3. Strongest possible reframing:
   - If the current framing is not sharp enough, propose a better one.
   - Should the title be "Safety Is a Claim, Not a Cost", "Which Actions Are Safe Enough", or something else?
   - What should Figure 1 show to make reviewers immediately understand the contribution?

4. Theory check:
   - Are the proposed propositions meaningful enough?
   - Is the deployability-gap negative result real or too obvious?
   - Is the global-vs-action calibration argument theoretically defensible?
   - What theorem would most increase the paper's perceived depth?

5. Experimental bar:
   - What experiments are absolutely required for oral-level credibility?
   - Is CAPS+ACCS necessary?
   - Which metrics are essential: certified utility area, claim yield, claim miscoverage, unsupported safety success, abstention, horizon risk?
   - What result pattern would make the paper compelling?
   - What result pattern would kill the paper?

6. Reviewer attack simulation:
   - Write the top 8 likely rejection arguments.
   - For each, say whether the current plan answers it.
   - If not, specify the exact fix.

7. Final action plan:
   - Give a prioritized list of changes to blueprint/theory/experiments.
   - Separate "must do before coding", "must do before main benchmark", and "nice-to-have oral polish".

Be direct and do not be encouraging unless the argument is actually strong. Assume I want to know the truth before spending server time.
```

## What To Ask After GPTPro Responds

If GPTPro gives useful feedback, ask a second focused question:

```text
Given your critique, please rewrite the paper's 6 contribution bullets and the Figure 1/Table 1 specification so that the paper has the highest possible chance of being seen as oral-level rather than incremental.
```
