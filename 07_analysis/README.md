# Analysis

- `score_pilot.py <runs dir> <out.csv>`: replays each run's edits onto the base repository and runs the independent oracle plus hidden tests. Reads `PILOT*` and `S2-*` task folders.
- `analyze_pilot.py` (Study 1, exploratory, 6 conditions) -> `pilot_v1_report.md`.
- `analyze_study2.py` (Study 2, frozen; H1-H3 confirmatory, rest exploratory) -> `study2_report.md` after the run.
Statistics: pairs are (task, run); task is the cluster; task-level sign-flip permutation test, task-clustered bootstrap CI, exact McNemar (descriptive), Holm correction. Pilot data are not pooled with Study 2.
