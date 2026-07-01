# Reviewer-Facing Claim Audit

> Date: 2026-07-01
> Scope: current AAAI draft after the mainline rewrite.
> Rule: every claim below must be backed by a theorem, a main-text number, an
> appendix table, or an explicit NEXT item. Unsupported claims are not allowed
> in the manuscript.

---

## Main Line

```text
A safety score is not a certificate. The certificate target is false safety
claims among actions or episodes actually issued after deployment-time
selection, under a frozen query law and continuation-label contract.
```

The current paper should be read as one strong claim plus supporting boundary
claims:

1. Post-selection issued-claim risk is the missing estimand.
2. ACCS is a finite-family audit layer for that estimand, reporting risk with
   yield and support accounting.
3. Action-level certificates do not automatically become trajectory
   certificates; emission budgets and closed-loop fixed-rule audits are the
   separate episode layer.
4. Negative cases are evidence: low-yield global CP, repaired toys, policy
   mismatch, no overlap, off-policy shift, COptiDICE failure, and DroneCircle
   rejection delimit what the certificate contract can honestly claim.

---

## Claim-by-Claim Audit

| Manuscript claim | Reviewer challenge | Existing answer to use | Current manuscript handling | Status |
|---|---|---|---|---|
| Learned safety/cost scores are not deployment certificates. | Is this more than rhetoric? | Exact K=16 toy: 4% per-action false certification becomes about 48% selected false certification; trained DSRL rows also show top-action false certification above candidate false. | Title, abstract, Introduction, Figure 1. | supported |
| Marginal conformal calibration does not control selected issued-claim risk. | Does ordinary conformal already solve it? | Theory selection-amplification theorem; toy; global CP baseline has low risk but only 3.8-8.1% yield in trained rows. | Problem Setup, Theory, Table 1, Audit Accounting. | supported |
| The target is issued-claim risk, not policy training quality. | Are we just evaluating safe RL reward/cost? | Formal ratio E[F]/E[I] plus yield; all baselines share frozen query banks. | Problem Setup and Experiments. | supported |
| ACCS controls risk for fixed finite rule families. | Is there a statistical guarantee? | Finite-family selective-risk theorem in paper and theory_proofs.md; audit/test split implementation. | Theory and Algorithm 1. | supported |
| ACCS is useful on trained safe-RL proposers. | Is it only a toy? | CAPSIQL/CPQ/COptiDICE direct OSRL table. CPQ q0.92: 7.17% top false to 2.25% ACCS at 80.18% yield. COptiDICE q0.92: 8.30% to 2.17% at 78.33% yield. | Abstract, Table 1, Experiments. | supported |
| Global CP is not the practical endpoint. | Is lower risk better regardless of yield? | Global CP has 0.08-0.13% risk but only 7.33-8.08% yield in CPQ/COptiDICE high-signal rows; CAPSIQL yield is 3.81%. | Table 1 and Audit Accounting. | supported |
| Reward-bin and CRC-style baselines are serious competitors. | Are baselines weak? | Toy hardening shows reward-bin/rank-bin/CRC repair the exact toy; Table 1 reports reward-bin and CRC. | Related Work, Experiments, Diagnostic Checks. | supported |
| Residual labels are continuation-policy dependent. | What if the label policy differs from deployment? | Local policy-mismatch diagnostic; explicit definition of Z_j under declared continuation policy. | Method and Diagnostic Checks. | supported |
| Unsupported actions cannot get distribution-free offline certificates. | Is support just a feature choice? | No-overlap proposition and diagnostic. | Theory and Diagnostic Checks. | supported |
| Residual-horizon changes do not collapse the action-level story. | Is the result fragile to H? | H=20/H=80 stress: ACCS remains below 5% on CPQ/COptiDICE with useful yield, while baselines become closer. | Main text paragraph plus appendix table. | supported |
| Action certificates do not imply episode certificates. | Does low block risk mean safe trajectories? | Logged episode proxy: CPQ ACCS has 2.25% block risk but 49.08% issued episode-proxy false rate; COptiDICE has 2.17% block risk but 44.37% episode-proxy false rate. | Experiments and Figure 2. | supported |
| Emission budgeting is a formal route to episode claims. | Is there theory and data for episode budgeting? | Episode-budgeted theorem; logged cap sweep: cap4 keeps episode-proxy false certification at 2.53% CPQ and 2.64% COptiDICE. | Theory, Experiments, Figure 2, appendix. | supported |
| Fixed-cap closed-loop certification can be positive in real online rollouts. | Is there true simulator evidence? | 4090 full-cap frontier: CPQ cap512 has CarCircle 12/600, U95 3.22%, and BallCircle 0/600, U95 0.50%, while saturating full episodes. | Abstract, Table 2, Figure 2. | supported |
| The audit rejects unsafe proposer/environment pairs. | Are failures hidden by abstention or omitted? | COptiDICE fails on Car/Ball/Drone; CPQ Drone cap512 is 90/600, U95 17.61%; tuned CPQ Drone improves to 32/395, U95 10.73%, still above target. | Table 2, Diagnostic/Conclusion sentence, appendix tuned-rule table. | supported |
| Off-policy deployment query laws require weighting/support checks. | What if audit and deployment query laws differ? | Local shift toy at a=8: unweighted P-audit has 33.90% risk at 41.19% yield under Q; known-ratio weighting has 4.45% at 28.49%; support cap has 0% at 27.23%. | Diagnostic paragraph plus appendix table; theorem in theory_proofs.md. | supported as diagnostic, not benchmark |
| SafeFQL is prior work but not yet a fair direct comparator. | Are we ignoring the most relevant competitor? | Public SafeFQL repo rechecked 2026-06-30/2026-07-01: README-only shallow clone, no runnable code/checkpoints/evaluator. | Related Work and Scope. | limitation documented |

---

## Claims That Must Not Be Made

| Unsupported claim | Why not | NEXT item |
|---|---|---|
| ACCS guarantees safe RL policies. | The guarantees are for issued action/episode claims under a declared query law, not arbitrary trajectories. | N3 claim-strength QA |
| ACCS dominates every selective baseline. | Reward-bin/CRC repair the toy and can be close under H=80. | Avoid; present risk-yield tradeoffs |
| The method handles arbitrary sequential distribution shift. | Only local off-policy query-shift support exists; broad online shift needs a larger protocol. | N5 claim-audit backlog |
| DroneCircle is a positive closed-loop environment. | Current best CPQ Drone tuned result is U95 10.73%, above the 5% target. | N1 higher-upside episode-audit frontier |
| SafeFQL has been beaten empirically. | No runnable public comparator is available yet. | N2 SafeFQL comparator status |

---

## Main-Text Placement Rule

Use main-text space for the strongest sentence per evidence object:

| Evidence object | Main-text handling | Appendix handling |
|---|---|---|
| Direct OSRL action audit | Full Table 1 and two interpretation paragraphs. | Per-row assets and stability rows. |
| Residual-horizon stress | One paragraph with H=20/H=80 numbers. | Full table. |
| Episode proxy and caps | One paragraph plus Figure 2 panel. | Full cap sweep. |
| Fixed-cap closed-loop | Full Table 2 and Figure 2 panel. | Full saturation sweep. |
| Tuned-rule closed-loop | One boundary sentence with 32/395, U95 10.73%. | Full tuned-rule table. |
| Off-policy shift | One diagnostic paragraph with a=8 numbers. | Full shift table and theorem details. |

---

## Next-Step Hooks From This Audit

1. If we want to claim broad deployment shift robustness, run a server-scale
   shift/off-policy audit or formalize a deployment density-ratio/support
   contract beyond the toy.
2. If we want a SafeFQL empirical comparison, wait for runnable code/checkpoints
   or build a fair, clearly labeled reimplementation.
3. If we want DroneCircle as a positive environment, design a method-level
   protocol beyond threshold/cap sweeps; repeating the same sweeps is not
   useful.
