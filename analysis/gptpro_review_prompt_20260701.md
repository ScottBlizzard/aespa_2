# Ready-To-Copy GPT Pro Prompt

你是一个从零开始阅读这个项目的顶会 ML/RL/AI safety 论文合作者和严苛审稿人。请不要假设你知道之前对话，也不要沿用任何外部记忆。

项目 GitHub: https://github.com/ScottBlizzard/aespa_2

请按这个顺序阅读：

1. `aaai2027/paper.pdf`
2. `aaai2027/appendix.pdf`
3. `idea_blueprint.md`
4. `experiment_report.md`
5. `analysis/reviewer_claim_audit_20260701.md`
6. `analysis/claim_evidence_map.md`
7. `theory_proofs.md`
8. `NEXT_STEPS.md`

如需追数字或细节，再看：

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

可选参考：`analysis/pro_review_2.md` 是上一轮外部 review，但请优先独立判断，不要被它锚定。

我的目标不是保守降级，也不是一上来收窄。我希望冲 AAAI oral 级别。请你在这个前提下客观判断：哪些东西已经有冲击力，哪些地方会被强审稿人打穿，以及最值得补的 1-3 个高上限动作是什么。除非确实必要，不要建议普通 threshold/cap sweep；如果建议实验，必须说明它能支撑什么更强 claim。

请重点回答：

1. 当前主线 "A safety score is not a certificate: calibration after action selection in offline RL" 是否有 AAAI oral 级别上限？如果有，最强 framing 是什么？如果没有，最能拔高上限的一个理论、实验或概念重构是什么？
2. 现在的 title/abstract/introduction 是否把论文打成了一个必须存在的 certificate evidence layer，还是仍然像 conformal thresholding 的小扩展？请给具体改写建议。
3. Novelty threat：请和 CAPS、SafeFQL、conformal risk control、selective conformal prediction、conformal safety shielding、conformal OPE、offline safe RL safety filters 对比。哪个最危险？需要怎么定位才能避免被说成已有工作？
4. 逐条 audit abstract/introduction/conclusion 里的 major claims：supported / overclaimed / needs experiment or theorem。请用项目里的 claim-evidence 文件作为起点，但按严苛审稿人标准重新判断。
5. 理论方面最该强化哪一块：selection amplification、finite-family selective risk、support/no-overlap、fixed-emission episode risk、off-policy weighting/support？请只选最有价值的一两个，并说明为什么。
6. 实验方面，Table 1、residual-horizon stress、episode proxy、fixed-cap closed-loop frontier 是否已经串成强证据链？如果下一轮可以用 8x4090，最高收益实验是什么？它会新增哪个主文 claim？
7. Episode-level story 怎么写最强又不夸大？CPQ Car/Ball 是 positive closed-loop evidence，COptiDICE 和 Drone 是 rejection/boundary evidence，这个组合应该放在主文里承担什么角色？
8. Off-policy query-shift toy 应该只作为 diagnostic paragraph，还是升级成 method-level contribution？如果升级，最小但有说服力的 server-scale protocol 是什么？
9. AAAI 正文 7 页限制下，哪些必须留主文，哪些进 appendix？已经跑出来但正文放不下的结果，如何用一句话或一个紧凑表格保留核心价值？
10. 请列出最可能导致 rejection 的 5 个问题，按严重程度排序，并给出最具体 fix：改写、定理、实验、baseline 或 limitation statement。
11. 最后只给 1-3 个 next actions。每个 action 都要说明目标 claim、所需最小工作量、成功/失败分别如何写进论文。

请按这个格式输出：

1. 一段 overall verdict：当前上限、最大短板、是否值得继续冲 oral。
2. 最强一-sentence thesis。
3. Title/abstract/introduction 的具体改写建议。
4. Novelty threat 表格。
5. Claim-support 表格。
6. Theory upgrade 建议。
7. Experiment upgrade 建议，包含 protocol sketch 和会支撑的 claim。
8. 7 页正文 placement plan。
9. Top-5 reviewer objections and fixes。
10. 最终 1-3 个 next actions。
