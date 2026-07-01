# NEXT_STEPS

> Last updated: 2026-07-01
> Scope: unfinished work and newly added next directions only.
> Rule: completed experiments and useful results belong in `experiment_report.md`; detailed chronology belongs in `analysis/reproduction_log.md`.
> Claim rule: every manuscript claim must be checked against existing evidence.
> If a claim has no supporting result/proof, either weaken/remove it in the
> manuscript or add the missing experiment/theory item here as unfinished work.

---

## Current Gate

The 4090 200/200 fixed-cap frontier has been extended to full-cap saturation
and integrated into the AAAI draft and appendix. The 2026-07-01 claim audit
also promoted a single tuned-rule boundary sentence and a single off-policy
shift diagnostic paragraph into the main paper. Do not repeat the finished
100/100 first-cap or 200/200 fixed-cap frontier runs unless they are used as
baselines inside a genuinely stronger protocol.

Next priority:

```text
paper/evidence QA is clean after the 2026-07-01 claim-audit rewrite:
`paper.pdf` is 8 pages with page 8 starting at References, and `appendix.pdf`
is 6 pages. Do not launch another 4090 batch unless it tests a method-level
protocol beyond threshold/cap sweeps. SafeFQL remains blocked by missing
runnable code.
```

Current compute context:

```text
4090 host: ccj@10.10.217.244
Project path: /home/ccj/workspace_1/aaai_2
Conda env: aaai2
Latest reconnect on 2026-07-01: host reachable, 8 x RTX 4090 idle, no active
AAAI_2 jobs. Remote tmux is not on the default PATH; use setsid/nohup plus log
files unless a login-shell tmux path is explicitly verified.
Backup A40 entry `ssh -p 10008 root@10.91.11.250` is also reachable.
Server hygiene: the 4090 directory is an experiment runner only. Keep `src/`,
`scripts/`, `external/`, `data/`, `outputs/`, and code-generated CSVs under
`analysis/paper_assets/`. Do not sync local paper drafts, `aaai2027/`, root
workflow Markdown, or `analysis/*.md` to the server. `push.ps1` now syncs only
experiment code.
Completed runs:
  RUN_ID=frontier_200x200_20260630_4090
  RUN_ID=frontier_drone_200x200_20260630_4090
  RUN_ID=frontier_caps64_200x200_20260630_4090
  RUN_ID=frontier_capsfull_200x200_20260630_4090
  RUN_ID=tuned_rule_100x200x200_20260630_4090
  RUN_ID=tuned_rule_drone_conservative_200x300x300_20260630_4090
  RUN_ID=tuned_rule_drone_medium_200x300x300_20260630_4090
```

---

## N1. Optional Higher-Upside Episode-Audit Frontier

Goal:

```text
Try to improve beyond fixed first-m-step rules while preserving a clean,
pre-registered audit story.
```

Current completed fixed-rule result:

```text
CPQ cap512 saturates full CarCircle/BallCircle episodes and passes exact test
CP95 <5%.
COptiDICE fails strongly on Car/Ball/Drone.
DroneCircle is a boundary diagnostic, not a third positive 5% case.
```

Current completed tuned-rule result:

```text
RUN_ID=tuned_rule_100x200x200_20260630_4090 completed 18/18 jobs with 0
failures. CPQ Car/Ball stay positive, but the tuned family does not improve the
main claim beyond fixed cap512. CPQ Drone improves from fixed-cap 90/600,
CP95 17.61% to 32/395, CP95 10.73%, but remains above the 5% target and is
seed-unstable.

Two focused Drone-only follow-ups also completed with 0 failures. The
conservative 200/300/300 search was too sparse: CPQ Drone 1/4 test false,
CP95 75.14%. The medium 200/300/300 search had CPQ Drone 54/581 test false,
CP95 11.52%. Neither reaches the 5% target.
```

Unfinished tasks:

1. Do not run more Drone tuning unless there is a new method-level idea, not
   just another threshold/cap sweep.
2. Keep DroneCircle as an honest harder-environment diagnostic in the appendix.
3. If a stronger episode-audit experiment is designed, it must introduce a new
   method dimension such as support/off-policy weighting, shift-triggered
   abstention, or a clearly pre-registered risk-allocation rule. Use the
   fixed-cap frontier as the baseline.

Acceptance criteria:

```text
No tuned-rule result is promoted unless a new protocol achieves independent
test CP95 <5% with nontrivial issued episodes. Current tuned-rule results are
diagnostic only.
```

---

## N2. SafeFQL Comparator Status

Goal:

```text
Resolve whether SafeFQL can become a direct comparator or only a positioned
prior-work discussion.
```

Current status:

```text
SafeFQL was re-checked on 2026-06-30/2026-07-01. The public repository HEAD is
106cef25ef8403b3384092e30201973a28f3dfae and the shallow clone at
external/SafeFQL contains only Readme.md. It still provides no runnable
training, checkpoint, evaluator, or dependency files for a fair direct
comparator.
```

Unfinished tasks:

1. Re-check the SafeFQL repository only at the next major paper freeze or if
   the authors announce runnable code/checkpoints.
2. If runnable code/checkpoints appear, adapt the same fixed query-bank and
   fixed-cap/frontier audit protocol.
3. If code remains unavailable, keep a precise no-code/no-checkpoint limitation
   paragraph.
4. Do not implement an approximate SafeFQL surrogate unless it can be made fair
   and clearly labeled.

Acceptance criteria:

```text
Either a fair SafeFQL result exists under the same protocol, or the paper has a
clean no-code/no-checkpoint limitation statement.
```

---

## N3. Paper And Evidence QA After Future Edits

Goal:

```text
Keep the 7-page AAAI draft synchronized with the evidence map and appendix
while avoiding arbitrary closed-loop safety claims.
```

Current clean state:

```text
The 2026-07-01 claim audit found no arbitrary closed-loop safety claim in the
abstract, introduction, closed-loop discussion, scope, or conclusion. The main
table still uses the fixed-cap saturation frontier. The tuned-rule diagnostic
is now a one-sentence boundary result in the main text and a full appendix
table. The off-policy shift toy is now a diagnostic main-text paragraph plus
appendix table, not a benchmark claim. The rebuilt paper is 8 pages with page 8
starting at References; the appendix is 6 pages.
```

Unfinished tasks after any future paper edit:

1. Re-run the claim-strength pass over `aaai2027/paper.tex`, especially
   abstract, conclusion, and scope paragraphs.
2. Preserve the hard layout invariant: 7 pages of body, page 8 starts with
   `References`.
3. Keep all tuned-rule and DroneCircle language diagnostic/boundary-only unless
   a new independent test result reaches CP95 <5% with nontrivial issued
   episodes.
4. Refresh `analysis/claim_evidence_map.md` whenever a new paper claim is added.
5. Refresh `analysis/reviewer_claim_audit_20260701.md` or create a dated
   successor whenever the main claims change.

Acceptance criteria:

```text
aaai2027/paper.pdf builds with no undefined citations and no overfull boxes.
Page 8 starts with References.
Appendix contains the full cap sweep and all promoted numbers are traceable.
```

---

## N4. Support/Off-Policy Shift Diagnostic

Goal:

```text
Raise the method beyond generic post-selection conformal auditing by showing how
support checks, bounded density ratios, or shift-triggered abstention change
issued-claim risk under deployment-query shift.
```

Current completed local result:

```text
`src/toy_offpolicy_shift.py` implements a deployment-query shift diagnostic.
At shift a=8, unweighted audit has 33.90% deployment false certification at
41.19% yield; known-ratio weighting tracks the oracle at 4.45% risk with
28.49% yield; a hard support cap gives 0% risk with 27.23% yield. This is a
good local theory-support result, not a reason to launch another 4090 batch.
It has been added to the appendix as a compact diagnostic table, promoted to a
single main-text diagnostic paragraph, and Theorem 5 in `theory_proofs.md` has
been polished to match the toy assumptions.
```

Unfinished tasks:

1. Do not promote this beyond a diagnostic paragraph unless it materially
   improves the core argument more than the current fixed-cap DSRL evidence.
2. If it is promoted into a formal method claim, convert Theorem 5 into final
   paper notation and add the exact assumptions to the proof appendix.
3. A server-scale shift audit is optional; run it only if it creates a new
   reviewer-visible claim beyond the local toy, no-overlap, and policy-mismatch
   diagnostics.

---

## N5. Claim-Audit Backlog

Goal:

```text
Keep unsupported high-upside claims visible without letting them leak into the
paper before we have evidence.
```

Unfinished claims requiring new evidence before manuscript promotion:

1. Broad sequential distribution-shift robustness. Current evidence is a local
   off-policy query-shift diagnostic, not a server-scale online shift audit.
2. Fair SafeFQL empirical comparison. This still requires runnable public
   checkpoints/code or a clearly labeled fair reimplementation.
3. DroneCircle as a positive 5% closed-loop environment. Current best CPQ tuned
   result is 32/395 test false issued episodes with CP95 10.73%, above target.
4. ACCS dominance over every selective baseline. This should not be claimed;
   reward-bin and CRC-style baselines are strong and sometimes close.

Acceptance criteria:

```text
Any manuscript sentence making one of these claims must cite a new experiment
or theorem. Otherwise weaken it, move it to future work, or delete it.
```

---

## Quality Gates After Every New Batch

Run after each completed experiment or paper edit:

```powershell
python -m py_compile src\run_dsrl_closed_loop_fixed_cap_audit.py src\run_dsrl_closed_loop_audit.py scripts\summarize_closed_loop_audit_outputs.py scripts\summarize_closed_loop_frontier_outputs.py
python -m py_compile src\run_dsrl_closed_loop_tuned_rule_audit.py scripts\summarize_closed_loop_tuned_rule_outputs.py
cd aaai2027
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -interaction=nonstopmode -halt-on-error appendix.tex
pdflatex -interaction=nonstopmode -halt-on-error appendix.tex
rg -n "undefined|Undefined|Citation|Reference|Overfull|LaTeX Warning|Package pgfplots Error|Package tikz Error|! LaTeX Error|Emergency stop|Rerun" paper.log paper.blg appendix.log
```

PDF checks:

```powershell
& 'C:\Program Files\MiKTeX\miktex\bin\x64\pdftoppm.exe' -png -r 170 aaai2027\paper.pdf outputs\render_checks\paper_4090_page
& 'C:\Program Files\MiKTeX\miktex\bin\x64\pdftoppm.exe' -png -r 170 aaai2027\appendix.pdf outputs\render_checks\appendix_4090_page
```

Server checks:

```powershell
ssh ccj@10.10.217.244 "conda run -n aaai2 python -V; pgrep -af '/home/ccj/workspace_1/aaai_2|run_dsrl|frontier' || true; nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader"
ssh -p 10008 root@10.91.11.250 "tmux ls || true; pgrep -af 'run_dsrl|frontier|python' || true; nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader"
```

Update only these files after each batch:

```text
experiment_report.md         completed useful results only
NEXT_STEPS.md                unfinished/new work only
analysis/reproduction_log.md detailed chronology and tmux/session logs
analysis/claim_evidence_map.md claim support status
analysis/paper_assets/README.md new paper-facing assets
```
