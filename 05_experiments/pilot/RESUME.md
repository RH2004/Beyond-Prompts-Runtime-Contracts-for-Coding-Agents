# STATUS 2026-11-14 (read first)
Study 1 (pilot_v1, 240 runs) is complete and scored. Phase 2 (pilot_v2) was stopped at 41 of 90 (free-tier cap). Study 2 (confirmatory) runs on OpenRouter DeepSeek under a 3 USD cap: see `05_experiments/README.md`, `00_protocol/lean_main_experiment_plan.md` and `00_protocol/study2_freeze.json`. The Gemini instructions below apply only to the old pilot.

Study 2 resume: from `03_framework/`, with the OpenRouter key in `GEMINI_KEYS` (the driver passes it as OPENROUTER_API_KEY): `python ../05_experiments/pilot/run_pilot.py --out ../05_experiments/study2/main --runs 1-2 --workers 6 --tasks S2-01,...,S2-14 --conditions C0,C1,C3,C4 --config study2_openrouter.yaml --budget 2.0`. Resumable.

# Pilot status and how to resume (stopped by the user, 2026-11-12)

## State
- Model: `gemini/gemini-3.1-flash-lite` via `03_framework/configs/pilot_gemini.yaml`. Keys are supplied only through the `GEMINI_KEYS` environment variable (comma-separated) and are never stored in the project.
- Tasks: PILOT-001..008 (`04_benchmark/tasks/`), each with hidden tests, a reference solution and an oracle (`04_benchmark/ground_truth/`). All references pass their oracle (`03_framework/tests/test_oracle.py`, 19 tests).
- Runs: `05_experiments/pilot/pilot_v1/`. Round 1 (run 1 of every task x condition, 48 cells) is complete and scored: `07_analysis/pilot_v1_runs.csv`. Round 2 started; 6 cells of it are complete and 6 were interrupted by the stop (they have no termination event; the driver quarantines them to `_infra_failed/` and redoes them on resume).
- Spend so far: about $0.70 in total on Gemini.

## Resume
From `03_framework/`, with the keys in the environment:
```bash
GEMINI_KEYS="key1,key2,key3,key4" .venv/Scripts/python ../05_experiments/pilot/run_pilot.py --out ../05_experiments/pilot/pilot_v1 --runs 2-5 --workers 6
```
Resumable: finished cells are skipped. Free-tier limits are 15 requests/minute per key (the driver pauses a key for 70 s) and probably a daily cap (the driver retires the key). Then score with
`03_framework/.venv/Scripts/python 07_analysis/score_pilot.py 05_experiments/pilot/pilot_v1 07_analysis/pilot_v1_runs.csv`.

## Open items to log in the decision log
1. PILOT-006 hidden test: the `domain: None` case was removed after round 1 because the prompt does not specify null handling; all conditions rescored identically (post-hoc correction).
2. PILOT-003 is a dependency trap (`email-validator` is not installed and there is no network). Every model imported it in round 1, so functional correctness cannot separate conditions on this task. Report it separately.
3. PILOT-002..008 were designed after PILOT-001 showed no violations (headroom). They are pilot tasks only; keep pilot data out of the main experiment.
4. Round-1 signal (n = 1 per cell, not a result): runs with an oracle-detected rule violation C0 5/8, C1 3/8, C1r 4/8, C2 3/8, C3 1/8, C4 0/8. Most of it is PERM-PATH-001 (edits to the protected test file). Check whether the effect extends to the other rules.

## Update 2026-11-14 (stopped again by the user until morning)
- State: 171 of 240 runs complete (rounds 1-3 complete = 144; round 4 = 27 of 48; round 5 not started). The 6 runs in flight at the stop have no termination event and are quarantined and redone on resume.
- Why it slowed: the free tier allows 500 requests per key per day; the first six keys used theirs up overnight. Two later keys carried round 4.
- Resume with all eight keys after the daily quota resets (Google resets at midnight Pacific time, about 08:00 local; verify by trying a key). Use `--workers 4` or fewer, and `--runs 4-5`. The driver escalates its pause for keys that keep failing (70 s, 140 s, ... up to 1 h).
- Phase 2 (not yet run): fixture `pilot_repo2`, tasks PILOT2-001..003, rules staged in `02_ekus/rules_phase2/` (move into `02_ekus/rules/` and run `python -m cec.stamp` only after pilot v1 finishes, so the rules-library hash stays constant during v1). Build the image with `docker build -f 03_framework/sandbox/Dockerfile --build-arg REPO=pilot_repo2 -t cec-pilot2:0.1 .` (done once; rebuild if the fixture changes). `run_pilot.py` picks the image per task.
- Incident: a malformed staged rule written into the live rules folder at about 23:10 on 2026-11-13 made a few round-4 runs fail at startup (infrastructure failures, redone). Fixed by staging rules outside the live folder.
