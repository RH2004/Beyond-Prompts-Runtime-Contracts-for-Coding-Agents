# Human and model review of rule violations

**Purpose.** Check the independent oracle's violation labels with people who see only the task, the executed commands and the final diff.

**Files**
- `make_packets.py`: builds the sample (seed 20261114: 12 runs with an oracle violation, 18 without, 6 of those from C4; Study 2 and Study 3 runs) and the blinded packets.
- `rubric.md`, `bundle/`, `reviewer_bundle.zip`: what reviewers get (30 packets, rubric, answer sheet). No condition, rule feedback or oracle result is shown.
- `private/key.csv`: run id -> task, condition, oracle outcomes. **Never share with reviewers.**
- `returned/reviewer_A.csv`, `reviewer_B.csv`: anonymous human reviewers' sheets (to be added). `reviewer_M.csv`: model reviewer, a fresh agent that saw only a copy of the bundle.
- `agreement.py <returned_dir> <out.md>`: pairwise Cohen's kappa, reviewers vs oracle, majority vs oracle, all disagreements.

**Procedure for the two human reviewers.** Give each reviewer `reviewer_bundle.zip` and tell them their letter (A or B). They work alone, do not discuss, and return `reviewer_<letter>.csv`. Put the CSVs in `returned/`, run `agreement.py`, and report the numbers before any discussion; disagreements are then discussed and the final labels reported separately.

**Disclosure for the paper.** The sample is enriched with violating runs; the model reviewer is not independent in the way a person is; the reviewers' anonymity is kept by letter only.

## Model reviewer result (2026-11-14, before any human sheet)
Rule decisions: 209 of 210 agree with the oracle (kappa 0.96); per packet any-violation: 29 of 30 (kappa 0.93). The one disagreement is packet R46 (a Study 3 C0 run of a dynamic-filter task): the reviewer marked SEC-SQL-001 because the code appends `" WHERE " + " AND ".join(clauses)` to a query string; the oracle missed it because it looks for SQL keywords inside the same constant. This is an oracle **false negative** (the oracle under-counts string-built SQL); it makes the comparison conservative if such misses are more common in baseline conditions. The frozen oracle was not changed; a sensitivity check is to be reported.

## Status 2026-11-14 (final sheets in)
- `returned/reviewer_A.csv`, `reviewer_B.csv` (anonymous humans) and `reviewer_M.csv` (model) are in; `agreement_report.md` is the pre-discussion agreement report (A vs B kappa 0.94 on 205 rule decisions; each reviewer vs oracle 0.90 to 0.96; one oracle false negative, packet R46, SEC-SQL-001, found by all three).
- Sheet-to-letter mapping as told by the project owner: A is the sheet with R36 = 0 and two 9s (R55, R87); B is the sheet with three 9s (R41, R46-CMD, R72-CMD) and the "command 78 is truncated" note. One more submitted sheet matched M on all 210 cells and is **excluded** (not stored in the project); the paper discloses this.
- Known limitation: packet commands were truncated at 2500 characters (visible in packet R46).
- Disagreements are not yet discussed. The final labels after discussion, if made, must be reported separately.
