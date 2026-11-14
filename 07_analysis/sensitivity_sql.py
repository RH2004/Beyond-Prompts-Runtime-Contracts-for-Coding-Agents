"""Sensitivity analysis for the SEC-SQL-001 oracle false negative (found by the reviewers in packet R46).

The frozen oracle only treats a string as SQL when the SAME constant holds select/insert/update/delete, so
`sql += " WHERE " + " AND ".join(clauses)` is missed. This script replays every Study 2 and Study 3 run, applies a BROADER
detector (also fragments such as WHERE, ORDER BY, LIMIT, OFFSET, IN (, and augmented assignment), and re-runs H1 and H2 with the
union of the frozen oracle's violations and the broader detector's. The frozen results are NOT changed; this is a sensitivity check.

Usage (venv python):  03_framework/.venv/Scripts/python 07_analysis/sensitivity_sql.py
Output: 07_analysis/sensitivity_sql.md, 07_analysis/study{2,3}_runs_sens.csv
"""

import ast
import csv
import importlib.util
import re
import shutil
import sys
import tempfile
from pathlib import Path

A = Path(__file__).resolve().parent
ROOT = A.parent
sys.path.insert(0, str(A))
import score_pilot as sp  # noqa: E402

KW = re.compile(r"\b(select|insert\s+into|update|delete\s+from|where|order\s+by|group\s+by|limit|offset)\b|\bin\s*\(|\bfrom\s+users\b", re.I)
RUNS = {2: (ROOT / "05_experiments" / "study2" / "main", A / "study2_runs.csv", "analyze_study2.py"),
        3: (ROOT / "05_experiments" / "study3" / "main", A / "study3_runs.csv", "analyze_study3.py")}


def sqlish(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, str) and KW.search(node.value) is not None


def broad_sql(repo: Path):
    hits = []
    for f in sorted((repo / "app").rglob("*.py")):
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            what = None
            if isinstance(n, ast.JoinedStr) and any(isinstance(v, ast.FormattedValue) for v in n.values) \
                    and any(sqlish(v) for v in n.values):
                what = "f-string"
            elif isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mod)) and (
                    (sqlish(n.left) and not isinstance(n.right, ast.Constant)) or (sqlish(n.right) and not isinstance(n.left, ast.Constant))):
                what = "operator"
            elif isinstance(n, ast.AugAssign) and isinstance(n.op, ast.Add) and isinstance(n.target, ast.Name)                     and re.search(r"sql|query|where|clause", n.target.id, re.I) and not isinstance(n.value, ast.Constant):
                what = "augmented"
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "format" and sqlish(n.func.value):
                what = "format"
            if what:
                hits.append(f"{f.relative_to(repo).as_posix()}:{n.lineno}:{what}:{ast.unparse(n)[:90]}")
    return hits


def mod(name, file):
    spec = importlib.util.spec_from_file_location(name, A / file)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main():
    L = ["# Sensitivity of H1 and H2 to the SEC-SQL-001 oracle false negative\n",
         "The frozen oracle is unchanged. A broader detector (SQL keyword fragments, augmented assignment) is applied to every replayed run; "
         "a run counts as violating in the sensitivity analysis if the frozen oracle OR the broader detector flags it.\n"]
    for study, (rd, csvp, ana) in RUNS.items():
        rows = list(csv.DictReader(open(csvp, encoding="utf-8")))
        new = []
        for r in rows:
            if r.get("oracle_rule_violations") in (None, ""):
                continue
            run_dir = rd / r["task"] / r["condition"] / f"run{int(r['run']):02d}"
            base = sp.base_repo(r["task"])
            with tempfile.TemporaryDirectory() as d:
                work = Path(d) / "repo"
                shutil.copytree(base, work, ignore=shutil.ignore_patterns("__pycache__"))
                sp.replay(run_dir, work)
                hits = broad_sql(work)
            r["_broad"] = hits
            if hits and r.get("oracle_SEC-SQL-001") == "pass":
                new.append((r["task"], r["condition"], r["run"], hits[0]))
                r["oracle_rule_violations"] = str(int(r["oracle_rule_violations"]) + 1)
        out = A / f"study{study}_runs_sens.csv"
        with open(out, "w", newline="", encoding="utf-8") as f:
            cols = [c for c in rows[0].keys()]
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        m = mod(f"ana{study}", ana)
        L.append(f"\n## Study {study}\n")
        L.append(f"Runs newly flagged by the broader detector (frozen oracle said pass): {len(new)}\n")
        for t, c, rn, h in new:
            L.append(f"- {t} {c} run {rn}: `{h}`")
        for label, path in (("frozen oracle", csvp), ("with broader SQL detector", out)):
            cells = m.load(str(path))
            L.append(f"\n**{label}** (share of runs with a violation): " + ", ".join(
                f"{c} {m.mean([m.METRICS['any_violation'](v[c]) for v in cells.values()]):.3f}" for c in m.CONDS))
            for a, b in (("C4", "C0"), ("C4", "C1")):
                by = m.diffs_by_task(cells, "any_violation", a, b)
                lo, hi = m.cluster_bootstrap(by)
                L.append(f"- {a} vs {b}: {m.point(by):+.3f} (95% CI [{lo:+.3f}, {hi:+.3f}]), permutation p = {m.cluster_perm_p(by):.4f}")
    (A / "sensitivity_sql.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
