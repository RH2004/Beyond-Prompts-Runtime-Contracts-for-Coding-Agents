# Study 3 plan (pre-registration, frozen before the first Study 3 run), 2026-11-14

## Why a third study, and what it can and cannot show
Study 2 (14 tasks, DeepSeek flash class) found violations in only 3 tasks: dynamic SQL (an ORDER BY built from a request value), tests added to the protected test file when the prompt asks for tests, and recursive forced deletes of scratch directories while testing file handlers. The confirmatory tests were underpowered because few tasks carried any signal. Study 3 asks the same question on **fresh tasks written to target those three situations**. Because the tasks were chosen after seeing Study 2, Study 3 describes *those situations*; it does not estimate how often violations happen in general and must not be pooled with Study 1 or Study 2.

## Design
- Model, harness and sandbox as in Study 2 (`openrouter/deepseek/deepseek-v4.1-flash`, `03_framework/configs/study2_openrouter.yaml`, image `cec-study2:0.1`, fixture `study2_repo` unchanged).
- Tasks: S3-01..S3-18 (`04_benchmark/tasks/`), 6 per situation: dynamic SQL (S3-01..06, rule SEC-SQL-001), tests requested while the visible test file is protected (S3-07..12, PERM-PATH-001), file-tree handlers (S3-13..18, PERM-CMD-001). Each has hidden tests, a reference solution and the independent oracle (same oracle as Study 2). Prompts name no rule or method (tests enforce this). Violation hypotheses are in each task's `notes`.
- Conditions: C0 (no rules), C1 (rules in the prompt), C4 (contracts enforced during execution). C3 is dropped to stay inside the budget; Study 2 already compares it.
- Runs: stage A is run 1 of every cell (18 x 3 = 54). Stage B (run 2, 54 more) is run only if the recorded cost of stage A is below 0.60 USD.
- Budget: the whole project is capped at 3 USD. OpenRouter usage before Study 3 was 1.49 USD. The driver runs with `--budget 1.1` (recorded Study 3 cost), so total usage stays below 2.7 USD.

## Hypotheses (Holm over H1-H2; H3 by confidence bound)
- H1: share of runs with at least one oracle violation is lower for C4 than for C0.
- H2: the same for C4 vs C1.
- H3: functional pass rate (hidden tests) of C4 is non-inferior to C0 (margin -0.10; lower 95% task-clustered bootstrap bound above -0.10).
Everything else (C1 vs C0, per-situation tables, cost, calls) is exploratory.

## Analysis (frozen)
`07_analysis/analyze_study3.py` on the output of `07_analysis/score_pilot.py`. Pairs are (task, run); task is the cluster; task-level sign-flip permutation test, task-clustered bootstrap CI, exact McNemar (descriptive), Holm. With 18 tasks the smallest attainable two-sided permutation p is about 8e-6, so the test can reach significance only if enough tasks show a difference.

## Human review
Same plan as the lean study: about 30 blinded runs sampled across Study 2 and Study 3, two human reviewers plus a fresh model reviewer, pre-discussion agreement reported.

## Threats
Tasks written by one person after seeing Study 2; one cheap model; the recursive-delete rule fires on scratch directories under /tmp, which is low-risk behaviour, so the CMD result measures rule compliance, not harm; the SQL rule counts any string-built SQL, including safe placeholder lists.
