"""Paired analysis of the pilot runs (decision 0017: paired comparisons, effect sizes, CIs, Holm; tasks are the clusters).

Usage: python 07_analysis/analyze_pilot.py 07_analysis/pilot_v1_runs.csv 07_analysis/pilot_v1_report.md

Unit of pairing: (task, run index). Only (task, run) pairs with all six conditions scored are used, so every contrast
is balanced. Uncertainty: a task-clustered bootstrap (resample tasks, then runs within tasks) because runs of one task
are not independent. Binary contrasts also get an exact McNemar test on the discordant pairs (descriptive: it ignores
clustering). Exploratory and not pre-registered: pilot data must not be pooled with the main experiment.
"""

import csv
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

CONDS = ["C0", "C1", "C1r", "C2", "C3", "C4"]
SCORED = {"submitted", "limits", "format_failure"}
RULES = ["PERM-PATH-001", "PERM-CMD-001", "ARCH-LAYER-001", "STY-LINT-001", "SEC-EVAL-001"]
# Planned contrasts (a, b): effect = metric(a) - metric(b)
CONTRASTS = [("C1", "C0"), ("C2", "C0"), ("C3", "C0"), ("C4", "C0"), ("C1", "C1r"), ("C3", "C1"), ("C4", "C1"),
             ("C4", "C2"), ("C4", "C3")]


def load(path):
    rows = [r for r in csv.DictReader(open(path, encoding="utf-8")) if r.get("termination") in SCORED
            and r.get("oracle_rule_violations") not in (None, "")]
    cell = defaultdict(dict)
    for r in rows:
        cell[(r["task"], int(r["run"]))][r["condition"]] = r
    return {k: v for k, v in cell.items() if all(c in v for c in CONDS)}


def num(r, k):
    return float(r.get(k) or 0)


METRICS = {
    "any_violation": lambda r: 1.0 if num(r, "oracle_rule_violations") > 0 else 0.0,
    "weighted_violations": lambda r: num(r, "oracle_weighted_violations"),
    "functional_pass": lambda r: num(r, "functional_pass"),
    "calls": lambda r: num(r, "calls"),
    "cost_usd": lambda r: num(r, "cost_usd"),
}


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def diffs_by_task(cells, metric, a, b):
    by = defaultdict(list)
    for (task, _), v in cells.items():
        by[task].append(METRICS[metric](v[a]) - METRICS[metric](v[b]))
    return by


def point(by):
    allv = [x for xs in by.values() for x in xs]
    return mean(allv)


def cluster_bootstrap(by, n=4000, seed=7):
    rng, tasks, out = random.Random(seed), list(by), []
    for _ in range(n):
        sample = []
        for t in (rng.choice(tasks) for _ in tasks):
            sample += [rng.choice(by[t]) for _ in by[t]]
        out.append(mean(sample))
    out.sort()
    return out[int(0.025 * n)], out[int(0.975 * n) - 1]


def mcnemar_exact(cells, a, b):
    only_a = only_b = 0
    for v in cells.values():
        x, y = METRICS["any_violation"](v[a]), METRICS["any_violation"](v[b])
        only_a += x == 1 and y == 0
        only_b += x == 0 and y == 1
    n = only_a + only_b
    if n == 0:
        return only_a, only_b, 1.0
    k = min(only_a, only_b)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
    return only_a, only_b, p


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def cluster_perm_p(by, n=20000, seed=11):
    """Task-level sign-flip permutation test on per-task mean differences (valid under clustering)."""
    rng = random.Random(seed)
    tm = [mean(v) for v in by.values()]
    obs = abs(mean(tm))
    if obs == 0:
        return 1.0
    hits = sum(abs(mean([x * rng.choice((-1, 1)) for x in tm])) >= obs - 1e-12 for _ in range(n))
    return (hits + 1) / (n + 1)


def main():
    cells = load(sys.argv[1])
    tasks = sorted({t for t, _ in cells})
    runs = sorted({r for _, r in cells})
    L = [f"# Pilot analysis (exploratory)\n", f"Complete (task, run) pairs: {len(cells)} = {len(tasks)} tasks x runs {runs}. "
         "Only pairs with all six conditions are used. Unit of analysis: task (cluster). Not pre-registered; pilot data are not pooled with the main experiment.\n"]
    L.append("## Per-condition means\n\n| Condition | any violation | weighted violations | functional pass | calls | cost USD |\n|---|---|---|---|---|---|")
    for c in CONDS:
        vals = [v[c] for v in cells.values()]
        L.append(f"| {c} | " + " | ".join(f"{mean([METRICS[m](r) for r in vals]):.3f}" for m in METRICS) + " |")
    for metric in ("any_violation", "weighted_violations", "functional_pass", "cost_usd"):
        L.append(f"\n## Contrasts: {metric} (a - b), paired by (task, run), task-clustered 95% bootstrap CI\n")
        L.append("| a vs b | difference | 95% CI | only a / only b | exact McNemar p | cluster permutation p | Holm p |\n|---|---|---|---|---|---|---|")
        res = []
        for a, b in CONTRASTS:
            by = diffs_by_task(cells, metric, a, b)
            lo, hi = cluster_bootstrap(by)
            oa, ob, pm = mcnemar_exact(cells, a, b) if metric == "any_violation" else (None, None, None)
            res.append((a, b, point(by), lo, hi, oa, ob, pm, cluster_perm_p(by)))
        adj = holm([r[8] for r in res])
        for r, h in zip(res, adj):
            a, b, d, lo, hi, oa, ob, pm, pp = r
            disc = f"{oa} / {ob}" if oa is not None else "-"
            L.append(f"| {a} vs {b} | {d:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {disc} | {'-' if pm is None else f'{pm:.4f}'} | {pp:.4f} | {h:.4f} |")
    L.append("\n## Violations by rule (count of runs, oracle)\n\n| Rule | " + " | ".join(CONDS) + " |\n|---|" + "---|" * len(CONDS))
    for rule in RULES:
        L.append(f"| {rule} | " + " | ".join(str(sum(1 for v in cells.values() if v[c].get("oracle_" + rule) == "fail")) for c in CONDS) + " |")
    L.append("\n## Runs with a violation by task (of runs per cell)\n\n| Task | " + " | ".join(CONDS) + " |\n|---|" + "---|" * len(CONDS))
    for t in tasks:
        row = [v for (tt, _), v in cells.items() if tt == t]
        L.append(f"| {t} (n={len(row)}) | " + " | ".join(str(int(sum(METRICS['any_violation'](v[c]) for v in row))) for c in CONDS) + " |")
    # variance components for planning the main experiment
    L.append("\n## Variance for planning (C0 any-violation rate)\n")
    rates = [mean([METRICS["any_violation"](v["C0"]) for (tt, _), v in cells.items() if tt == t]) for t in tasks]
    within = mean([r * (1 - r) for r in rates])
    between = mean([(r - mean(rates)) ** 2 for r in rates])
    L.append(f"Between-task variance of the C0 violation rate: {between:.3f}; mean within-task Bernoulli variance: {within:.3f}. "
             f"Task heterogeneity is {'large' if between > within else 'moderate'}: the main experiment needs enough tasks, not just more runs per task.")
    L.append("\n## Limits\n\n- One model, one fixture repository, task set designed after PILOT-001 showed no violations (headroom).\n"
             "- Violations come mostly from the path and command rules; the others have too few events to compare.\n"
             "- Several prompts ask for tests while the only test file is protected (rule/task tension), and PILOT-003 is a dependency trap.\n"
             "- The in-repo docstring of `handlers.py` states the layering rule, so C0 is not fully rule-blind for ARCH-LAYER-001.\n")
    Path(sys.argv[2]).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
