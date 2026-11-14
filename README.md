# Beyond Prompts: Runtime Contracts for Coding Agents (replication artifact)

**Purpose.** This repository exists only to let others replicate and check the results of the paper *Beyond Prompts: Runtime Contracts for Coding Agents* by Reda Heddad. It contains what is needed to re-derive every number in the paper: the framework, tasks, hidden tests, independent oracles, frozen protocols, every run log, the scoring and analysis scripts, the review kit and the manuscript source. Planning memos, literature screening records, drafts and working notes are deliberately not included.

**Question studied.** Do executable engineering contracts enforced while a coding agent works reduce rule violations compared with the same rules given as prompt text, retrieved as guidance, or checked only after generation?

**Studies** (never pooled; see `00_protocol/` and `05_experiments/README.md`)

| Study | Tasks | Conditions | Runs | Model |
|---|---|---|---|---|
| 1, exploratory | 8 | C0, C1, C1r, C2, C3, C4 | 240 | Gemini 3.1 Flash-Lite |
| 2, confirmatory | 14 | C0, C1, C3, C4 | 112 | DeepSeek v4.1 Flash (OpenRouter) |
| 3, confirmatory, targeted | 18 | C0, C1, C4 | 108 | DeepSeek v4.1 Flash (OpenRouter) |

Each confirmatory study's plan, tasks, configuration and analysis script were hashed before its first run (`00_protocol/study2_freeze.json`, `study3_freeze.json`).
A partial phase 2 of Study 1 (`05_experiments/pilot/pilot_v2`, 41 of 90 runs) was stopped because of free-tier quota limits and is not part of any reported result. Folders named `_infra_failed` hold attempts that failed for infrastructure reasons (quota or network errors) and were redone; they are kept for transparency and are not analysed.

## Layout

| Folder | Content |
|---|---|
| `00_protocol/` | Plans, decision log (deviations and results), freeze manifests |
| `02_ekus/` | The rule library (executable contracts) and schema |
| `03_framework/` | Agent contract layer, configurations, sandbox Dockerfile, tests |
| `04_benchmark/` | Tasks, hidden tests, reference solutions, oracles, fixtures, builders (`study2_build.py`, `study3_build.py`) |
| `05_experiments/` | Driver, and every run log of Studies 1 to 3 |
| `06_evaluation/review/` | Blinded review kit, anonymous reviewer sheets, agreement script and report |
| `07_analysis/` | Scoring and analysis scripts, scored CSVs, reports, sensitivity analysis |
| `08_paper/` | Manuscript source and figure scripts |

## Licenses

| What | License |
|---|---|
| Software: `03_framework/src`, `03_framework/tests`, `05_experiments/pilot/run_pilot.py`, `06_evaluation/review/*.py`, `07_analysis/*.py`, `08_paper/figures/*.py`, `tools/`, builders in `04_benchmark/*.py` | PolyForm Noncommercial 1.0.0 (`LICENSE`) |
| Everything else (rules, tasks, fixtures, ground truth, logs, review data, reports, figures, paper source, documents) | CC BY-NC 4.0 (`LICENSE-DATA.md`) |

Both require credit. **Commercial use requires a separate written license:** see `COMMERCIAL.md`.
Please cite the paper and this repository (`CITATION.cff`).

## Reproducing the analysis (no API key needed)

1. Python 3.14 environment: `python -m venv .venv`, then `pip install -r 03_framework/requirements.lock`.
2. Re-score runs: `python 07_analysis/score_pilot.py 05_experiments/study3/main 07_analysis/study3_runs.csv` (replays logged edits onto the base repository and runs each task's oracle and hidden tests).
3. Re-run the frozen analyses: `python 07_analysis/analyze_study3.py 07_analysis/study3_runs.csv out.md` (and `analyze_study2.py`, `analyze_pilot.py`).
4. Rebuild figures: `python 08_paper/figures/make_figures.py` (needs matplotlib).
5. Framework tests: `cd 03_framework && python -m pytest tests -q`.

## Re-running the agents (needs Docker and a model API key)

Build the sandbox image and run the driver (the key is read only from the environment):

```
docker build -f 03_framework/sandbox/Dockerfile --build-arg REPO=study2_repo -t cec-study2:0.1 .
cd 03_framework
GEMINI_KEYS="<your OpenRouter key>" python ../05_experiments/pilot/run_pilot.py --out ../05_experiments/study3/main2 \
  --runs 1-2 --workers 6 --tasks S3-01,S3-02 --conditions C0,C1,C4 --config study2_openrouter.yaml --budget 1.1
```

(The variable is named `GEMINI_KEYS` for historical reasons; the driver passes it as the provider key.) A full repeat of Studies 2 and 3 cost about 2.2 USD in model fees at the time of the study. Model behaviour and prices change, so exact reproduction of agent runs is not guaranteed; this is why all logs are included.

## Known limitations

One low-cost model per study, one small Python fixture, tasks written by one author, an oracle that shares rule definitions with the enforced checks (one known false negative, reported in the paper), and human review of 30 runs. See the paper's threats section and `00_protocol/decisions/decision_log.md`.

## Contact

reda0heddad@gmail.com
