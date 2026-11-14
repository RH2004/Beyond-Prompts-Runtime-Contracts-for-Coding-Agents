# Paper source

`main.tex` is the manuscript source (IEEEtran conference class; the bibliography is inside the file). `figures/` holds the figures as PDF and PNG and the script that regenerates them from the scored CSVs in `07_analysis/` (`python 08_paper/figures/make_figures.py`, needs matplotlib). `figures/check_tex.py` runs simple static checks on the source.

Where each number in the paper comes from:

| Paper item | Source |
|---|---|
| Study 1 table | `07_analysis/pilot_v1_report.md` (240 runs) |
| Study 2 table and H1 to H3 | `07_analysis/study2_report.md` (112 runs) |
| Study 3 table and H1 to H3 | `07_analysis/study3_report.md` (108 runs) |
| Oracle sensitivity analysis | `07_analysis/sensitivity_sql.md` |
| Human review | `06_evaluation/review/agreement_report.md` |
| Frozen protocols | `00_protocol/lean_main_experiment_plan.md`, `study2_freeze.json`, `study3_plan.md`, `study3_freeze.json` |
