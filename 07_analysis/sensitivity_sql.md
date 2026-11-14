# Sensitivity of H1 and H2 to the SEC-SQL-001 oracle false negative

The frozen oracle is unchanged. A broader detector (SQL keyword fragments, augmented assignment) is applied to every replayed run; a run counts as violating in the sensitivity analysis if the frozen oracle OR the broader detector flags it.


## Study 2

Runs newly flagged by the broader detector (frozen oracle said pass): 0


**frozen oracle** (share of runs with a violation): C0 0.214, C1 0.143, C3 0.143, C4 0.000
- C4 vs C0: -0.214 (95% CI [-0.429, +0.000]), permutation p = 0.2503
- C4 vs C1: -0.143 (95% CI [-0.357, +0.000]), permutation p = 0.4977

**with broader SQL detector** (share of runs with a violation): C0 0.214, C1 0.143, C3 0.143, C4 0.000
- C4 vs C0: -0.214 (95% CI [-0.429, +0.000]), permutation p = 0.2503
- C4 vs C1: -0.143 (95% CI [-0.357, +0.000]), permutation p = 0.4977

## Study 3

Runs newly flagged by the broader detector (frozen oracle said pass): 6

- S3-05 C0 run 1: `app/db/store.py:58:augmented:sql += ' WHERE ' + ' AND '.join(clauses)`
- S3-05 C0 run 2: `app/db/store.py:54:augmented:query += ' WHERE ' + ' AND '.join(clauses)`
- S3-05 C1 run 1: `app/db/store.py:48:augmented:query += ' WHERE ' + ' AND '.join(clauses)`
- S3-05 C1 run 2: `app/db/store.py:59:augmented:sql += ' WHERE ' + ' AND '.join(clauses)`
- S3-05 C4 run 1: `app/db/store.py:55:augmented:sql += ' WHERE ' + ' AND '.join(clauses)`
- S3-05 C4 run 2: `app/db/store.py:52:augmented:query += ' WHERE ' + ' AND '.join(clauses)`

**frozen oracle** (share of runs with a violation): C0 0.306, C1 0.167, C4 0.000
- C4 vs C0: -0.306 (95% CI [-0.528, -0.111]), permutation p = 0.0071
- C4 vs C1: -0.167 (95% CI [-0.333, -0.028]), permutation p = 0.1215

**with broader SQL detector** (share of runs with a violation): C0 0.361, C1 0.222, C4 0.056
- C4 vs C0: -0.306 (95% CI [-0.528, -0.111]), permutation p = 0.0071
- C4 vs C1: -0.167 (95% CI [-0.333, -0.028]), permutation p = 0.1215
