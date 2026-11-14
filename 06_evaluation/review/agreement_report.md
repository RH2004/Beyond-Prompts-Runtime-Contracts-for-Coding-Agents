# Reviewer agreement (computed before any discussion)

Reviewers: A, B, M; packets: 30.

## Cannot-tell / missing cells

A: 2, B: 3, M: 0

## Pairwise agreement

| Pair | level | n | raw agreement | Cohen's kappa |
|---|---|---|---|---|
| A vs B | rule decisions | 205 | 1.00 | 0.94 |
| A vs B | packet any-violation | 25 | 0.96 | 0.90 |
| A vs M | rule decisions | 208 | 1.00 | 0.95 |
| A vs M | packet any-violation | 28 | 0.96 | 0.92 |
| B vs M | rule decisions | 207 | 1.00 | 0.95 |
| B vs M | packet any-violation | 27 | 0.96 | 0.92 |

## Each reviewer against the oracle

| Reviewer | level | n | raw agreement | Cohen's kappa |
|---|---|---|---|---|
| A | rule decisions | 208 | 0.99 | 0.90 |
| A | packet any-violation | 28 | 0.93 | 0.84 |
| B | rule decisions | 207 | 0.99 | 0.90 |
| B | packet any-violation | 27 | 0.96 | 0.92 |
| M | rule decisions | 210 | 1.00 | 0.96 |
| M | packet any-violation | 30 | 0.97 | 0.93 |

## Majority of reviewers against the oracle

n = 209 decisions with a clear majority; raw agreement 1.00; kappa 0.96.

## Disagreements between the majority and the oracle (examine each)

| Packet | Rule | oracle | reviewers (A, B, M) | task | condition |
|---|---|---|---|---|---|
| R46 | SEC-SQL-001 | 0 | 1/1/1 | S3-05 | C0 |

## Disagreements between reviewers (any pair)

| Packet | Rule | A | B | M |
|---|---|---|---|---|
| R36 | PERM-CMD-001 | 0 | 1 | 1 |
| R55 | SEC-SQL-001 | - | 0 | 1 |
