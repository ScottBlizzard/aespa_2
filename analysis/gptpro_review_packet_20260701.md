# GPT Pro Review Packet

Date: 2026-07-01

Purpose: give GPT Pro a from-scratch, reviewer-facing view of the current AAAI
2027 paper and ask for high-upside upgrades. The target is not a conservative
workshop/narrowing review. The target is an oral-level AAAI paper if the idea,
theory, and evidence can support it.

## Repository

GitHub: https://github.com/ScottBlizzard/aespa_2

Use the latest pushed state of the main branch unless a newer branch is
explicitly provided.

## Read Order

Read these first:

1. `aaai2027/paper.pdf`
2. `aaai2027/appendix.pdf`
3. `idea_blueprint.md`
4. `experiment_report.md`
5. `analysis/reviewer_claim_audit_20260701.md`
6. `analysis/claim_evidence_map.md`
7. `theory_proofs.md`
8. `NEXT_STEPS.md`

If more detail is needed, read:

1. `aaai2027/paper.tex`
2. `aaai2027/appendix.tex`
3. `aaai2027/tikz_figures.tex`
4. `analysis/paper_assets/README.md`
5. `analysis/paper_assets/table_main_direct_osrl.csv`
6. `analysis/paper_assets/table_dsrl_horizon_stress.csv`
7. `analysis/paper_assets/table_dsrl_episode_capsweep_proxy_car_q92.csv`
8. `analysis/paper_assets/table_dsrl_closed_loop_fixed_cap_frontier_capsfull_200x200_20260630_4090.csv`
9. `analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_tuned_rule_100x200x200_20260630_4090.csv`
10. `analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_tuned_rule_drone_conservative_200x300x300_20260630_4090.csv`
11. `analysis/paper_assets/table_dsrl_closed_loop_tuned_rule_tuned_rule_drone_medium_200x300x300_20260630_4090.csv`

Optional context:

1. `analysis/pro_review_2.md`, if you want to see the previous outside review.
   Do not let it bias an independent assessment.

Do not spend time on raw `outputs/`, checkpoints, datasets, or server logs
unless a specific number in the paper cannot be traced through the files above.

## Current Paper Thesis

A safety score is not a deployment certificate. Offline safe RL systems often
learn cost/safety scores and then select actions from a candidate bank, but the
statistical target for deployment is false certification among the actions or
episodes actually issued after selection. The paper proposes a post-selection
audit layer for this issued-claim target, with explicit yield, support, and
residual-policy accounting.

## Current Strongest Evidence

- Exact selection toy: 4% per-action false certification becomes about 48%
  selected false certification when selecting the best of 16 reward-ranked
  candidates.
- Official DSRL CarCircle direct audit:
  - CPQ q0.92: top selected false 7.17%, ACCS-v0 2.25% risk at 80.18% yield.
  - COptiDICE q0.92: top selected false 8.30%, ACCS-v0 2.17% risk at 78.33%
    yield.
  - Global CP controls risk mostly by low yield, about 3.8-8.1% in the main
    trained rows.
- Residual-horizon stress: CPQ/COptiDICE H=20 and H=80 remain below 5% under
  ACCS with useful yield, but baselines get closer at H=80.
- Logged episode proxy: action-level ACCS risk around 2.2% can accumulate to
  49.08%/44.37% episode-proxy false certification without emission caps.
- Fixed-cap closed-loop frontier on 8x4090:
  - CPQ cap512 saturates full CarCircle episodes: 12/600 test false, exact
    CP95 upper bound 3.22%.
  - CPQ cap512 saturates full BallCircle episodes: 0/600 test false, exact
    CP95 upper bound 0.50%.
  - COptiDICE fails strongly on CarCircle/BallCircle/DroneCircle.
  - CPQ DroneCircle remains a boundary case: fixed cap512 90/600, CP95 17.61%;
    broad tuned rule improves to 32/395, CP95 10.73%, still above the 5%
    target.
- Off-policy query shift toy:
  - At shift `a=8`, unweighted audit has 33.90% deployment false certification
    at 41.19% yield.
  - Known-ratio weighting gives 4.45% risk at 28.49% yield.
  - Hard support cap gives 0% risk at 27.23% yield.

## Known Constraints

- AAAI main body is 7 pages. In the current build, `paper.pdf` is 8 pages and
  page 8 starts with References. The body is full and must not exceed the limit.
- `appendix.pdf` is 6 pages.
- SafeFQL public repository was rechecked on 2026-06-30/2026-07-01 and the
  shallow clone is README-only, with no runnable comparator code, checkpoint,
  evaluator, or dependencies.
- DroneCircle is not currently a positive 5% closed-loop environment.
- The paper must not claim general safe-RL policy safety, arbitrary sequential
  shift robustness, empirical dominance over SafeFQL, or universal superiority
  over CRC/reward-bin style selective baselines.

## Questions For GPT Pro

1. Oral-level ceiling:
   Is the main line "calibration after action selection for issued safety
   certificates" strong enough for an AAAI oral-level paper if written and
   supported well? If yes, what is the strongest possible framing? If no, what
   one theorem, experiment, or conceptual reframing would most increase the
   ceiling?

2. Main-line force:
   Does the current title/abstract/introduction make the paper feel like a
   necessary new evidence layer for offline safe RL, or does it still feel like
   a modest conformal thresholding extension? Give exact rewrite advice.

3. Novelty threats:
   Compare the paper against CAPS, SafeFQL, conformal risk control, selective
   conformal prediction, conformal safety shielding, conformal OPE, and offline
   safe RL safety filters. Which prior work is the most dangerous overlap, and
   what sentence-level positioning should neutralize that risk?

4. Claim-support audit:
   For every major claim in the abstract/introduction/conclusion, classify it
   as supported, overclaimed, or needing one more experiment/theorem. Use
   `analysis/reviewer_claim_audit_20260701.md` and
   `analysis/claim_evidence_map.md` as the starting point, but be adversarial.

5. Theory spine:
   Is the current theorem stack enough for a top AAAI paper, or should the
   theory be upgraded around support/no-overlap, finite-family selective risk,
   fixed-emission episode risk, or off-policy weighting? Name the single most
   valuable theorem to add or sharpen.

6. Experiment spine:
   Are Table 1, residual-horizon stress, episode proxy, and fixed-cap
   closed-loop frontier enough as a coherent evidence chain? What is the single
   highest-upside next experiment if we can use 8x4090, and what exact claim
   would it enable?

7. Episode-level story:
   Is the fixed-cap closed-loop result strong enough to be a main-text pillar,
   or should it be framed as a boundary audit? How should we phrase CPQ
   Car/Ball positive results while honestly keeping Drone and COptiDICE
   failures?

8. Shift/support story:
   Should the off-policy query-shift toy stay as a diagnostic paragraph, or
   should it become a method-level contribution with a server-scale experiment?
   If promoted, what exact protocol would make it reviewer-visible?

9. Seven-page placement:
   Given the AAAI 7-page body limit, what must stay in the main text, what
   should move to the appendix, and what one sentence or compact table can keep
   each useful completed result visible?

10. Rejection risks:
    List the top five likely reviewer objections, ordered by severity, and give
    the most concrete fix for each: rewrite, theorem, experiment, baseline, or
    limitation statement.

11. Next-step priority:
    Choose only 1-3 next actions. Do not suggest another threshold/cap sweep
    unless it changes the method dimension. Prefer high-upside actions that can
    materially raise the paper's ceiling.

## Desired Output Format From GPT Pro

Please answer in this structure:

1. One-paragraph verdict on the paper's current ceiling.
2. Strongest possible one-sentence thesis.
3. Main-line rewrite advice for title/abstract/introduction.
4. Novelty-threat table with prior work, risk, and positioning fix.
5. Claim-support table with status and required fix.
6. Theory upgrade recommendation.
7. Experiment upgrade recommendation, including the exact claim it would
   support and the minimal protocol.
8. Seven-page main-text placement plan.
9. Top five rejection risks and fixes.
10. Final 1-3 concrete next steps.
