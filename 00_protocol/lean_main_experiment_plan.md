# Lean confirmatory study (Study 2): plan to freeze before any confirmatory run

Status: **Frozen 2026-11-14 (see Revision and study2_freeze.json).** Freeze (hash and date) before the first confirmatory run. Nothing below may change after the freeze except through a logged amendment.

## Revision 2026-11-14 (budget-driven; supersedes sections 2, 3, 4, 5, 6 and 9 where they differ)
The free tier proved too slow (500 requests per key per day) and the project owner set a hard budget of **3 USD** for the whole study. Study 2 therefore runs as follows. Everything else in this plan stands.
- **Model:** `openrouter/deepseek/deepseek-v4.1-flash` (config `03_framework/configs/study2_openrouter.yaml`, temperature 1.0, seed 1000 + run index, per-run cost cap 0.08 USD). Study 1 used Gemini 3.1 Flash-Lite, so Study 2 is also a replication on a second model. Cost per run measured in smoke tests: 0.005 to 0.024 USD.
- **Tasks:** 14 fresh tasks S2-01..S2-14 on a new fixture `study2_repo` (neutral docstrings), 7 rules with 2 tasks each (SEC-SQL, SEC-SECRET, SEC-SHELL, SEC-EVAL, ARCH-LAYER, PERM-PATH, PERM-CMD); no rule has more than 14% of the tasks. Two tasks (S2-11, S2-12) ask for tests while the visible test file is protected (tension stratum). Each task has hidden tests, a reference solution and the independent oracle; `03_framework/tests/test_study2.py` (59 tests) checks them. The violation hypothesis of each task is in its yaml `notes`, written before any Study 2 run.
- **Conditions:** C0, C1, C3, C4 (C1r and C2 dropped: Study 1 already covers them).
- **Runs:** 14 tasks x 4 conditions x 2 runs = **112 runs** (about 1.4 USD expected). A third run per cell (168 runs in total) is added only if the recorded cost after the first 112 is below 1.6 USD; the driver refuses to start runs once the recorded cost plus an in-flight margin would exceed the budget (`--budget`).
- **Hypotheses (Holm over H1-H2; H3 by confidence bound):** H1 C4 has a lower share of runs with at least one oracle violation than C0; H2 the same for C4 vs C1; H3 functional pass rate of C4 is non-inferior to C0 (margin -0.10; lower 95% task-clustered bootstrap bound above -0.10). H3 of the earlier text (C1 vs C1r) is dropped. Everything else is exploratory.
- **Analysis script:** `07_analysis/analyze_study2.py` (frozen); scoring `07_analysis/score_pilot.py`.
- **Freeze:** hashes of plan, tasks, ground truth, fixture, config, rules, driver and analysis scripts are in `00_protocol/study2_freeze.json`, written before the first Study 2 run.

The earlier 8-task and 3-task pilots are **Study 1 (exploratory)**. They are reported separately and never pooled with Study 2.

## 1. Claim this study can support
A small, controlled comparison on one model: *does enforcing engineering contracts while an agent works reduce rule violations compared with putting the same rules in the prompt, and what does it cost?* It does **not** test other models, languages, real repositories or retrieval of guidance (C2 is dropped for the lean version; Study 1 showed C2 behaving like C1).

## 2. Hypotheses (confirmatory) and other analyses
| ID | Contrast | Metric | Direction |
|---|---|---|---|
| H1 | C4 vs C0 | share of runs with at least one oracle-detected rule violation | C4 lower |
| H2 | C4 vs C1 | same | C4 lower |
| H3 | C1 vs C1r | same | no benefit from rule content (reported with CI; equivalence margin 0.15) |
| H4 | C4 vs C0 | functional pass rate (hidden tests) | non-inferiority, margin -0.10 |

Holm correction over H1-H4. Exploratory (labelled as such): C3 vs C4 (prevention vs detection: violations by commands that had already run), weighted violations, cost, calls, wall-clock, false blocks, recovery after a block, per-rule effects.

## 3. Conditions (identical agent, flags only)
C0 no rules; C1 rules in the prompt; C1r irrelevant rules in the prompt (length-matched control); C3 executable checks after generation with a shared feedback budget; C4 contracts enforced during execution with the same budget. Config: `03_framework/configs/pilot_gemini.yaml` (model `gemini/gemini-3.1-flash-lite`, temperature 1.0, seed 1000 + run), frozen with its hash.

## 4. Tasks (frozen first, then run)
- **At least 16 tasks**, each a repository feature or fix with hidden tests, a reference solution and an oracle whose check method differs from the in-loop check.
- **Rule spread:** at least 8 distinct rules in the library, each exercised by at least 2 tasks; no single rule accounts for more than 25% of the tasks.
- **No rule-revealing text** in repositories (comments, docstrings, README). Prompts never name a rule or a method (tests enforce this).
- At most 4 tasks may ask for tests while a test file is protected (the rule/task-tension stratum, reported separately).
- Every task has a deterministic oracle; the reference passes all checks and the base fails the hidden tests (automated tests).
- Tasks are written from pre-declared violation hypotheses ("the shortest approach would break rule X"). Task writers do not look at Study 2 results; any task found invalid after the freeze is dropped for all conditions, with the reason logged.
- A dependency trap or other task that makes functional correctness unattainable for every condition is excluded from H4.

## 5. Runs
16 tasks x 5 conditions x 3 runs = **240 runs**, run-index-major with a fixed shuffle within each run index (`05_experiments/pilot/run_pilot.py`). About 17 requests per run, about 4,100 requests in total: one to two days on the free tier. Infrastructure failures are logged, set aside and redone; step-limit runs count as normal data.

## 6. Analysis (pre-specified)
Pairs are (task, run). Task is the cluster. Primary inference: task-level sign-flip permutation test on per-task mean differences; 95% task-clustered bootstrap CIs; Holm over H1-H4. Also report exact McNemar (descriptive) and effect sizes. Minimum effect of interest: a 0.20 absolute difference in violation share. Script: `07_analysis/analyze_pilot.py` (frozen with the plan).

## 7. Human review
Two reviewers independently judge a random sample of 24 runs (blind to condition) for rule violations and for whether the oracle and the reviewers agree; report Cohen's kappa (target at least 0.6). If a second reviewer is unavailable, say so as a limitation.

## 8. Threats to validity and mitigations
- One cheap model; results may not carry over to stronger models. Mitigation: a smaller subset on a second model is optional and reported separately.
- Tasks written by one person against known failure modes: mitigated by pre-declared hypotheses, oracle independence and the freeze.
- Free-tier provider: model weights and serving can change; record model id, date and provider usage metadata with every run.
- Rule-based enforcement can block safe code: measure false blocks; do not hide them.

## 9. Cost and timeline
Budget: $0 on free-tier keys (about $5 if one paid key is used instead). Order: finish Study 1 phase 2; write 16 tasks and oracles; freeze (hash, date); run (1-2 days); analyse; write the report. Key use must comply with the provider's terms; the project owner is responsible for confirming that.
