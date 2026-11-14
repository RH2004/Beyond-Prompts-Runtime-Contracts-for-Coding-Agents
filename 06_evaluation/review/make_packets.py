"""Builds the blinded human/model review packets (seeded sample of Study 2 and Study 3 runs).

Usage (from the QCA root, venv python):  03_framework/.venv/Scripts/python 06_evaluation/review/make_packets.py

Outputs
  06_evaluation/review/bundle/   WHAT REVIEWERS GET: packets/R01.md ..., rubric.md, answer_sheet_template.csv
  06_evaluation/review/private/  WHAT REVIEWERS MUST NOT SEE: key.csv (run id -> task/condition/run, oracle outcomes)

Sample (seed 20261114): 30 runs = 12 runs with at least one oracle violation + 18 runs without (6 of them from C4, the rest from
C0/C1/C3). The sample is enriched with violating runs on purpose so that agreement is not trivially "no violation"; this is stated
in the paper. Packet order is shuffled and ids are random-looking, so neither order nor id reveals the condition.
A packet shows only: the task text, the shell commands the agent actually executed, and the final repository change (diff). It
shows no condition label, no rule feedback and no oracle result.
"""

import csv
import difflib
import json
import random
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "07_analysis"))
import score_pilot as sp  # noqa: E402

OUT = ROOT / "06_evaluation" / "review"
BUNDLE, PRIVATE = OUT / "bundle", OUT / "private"
RUNS = {"S2": ROOT / "05_experiments" / "study2" / "main", "S3": ROOT / "05_experiments" / "study3" / "main"}
CSVS = [ROOT / "07_analysis" / "study2_runs.csv", ROOT / "07_analysis" / "study3_runs.csv"]
RULES = ["ARCH-LAYER-001", "SEC-EVAL-001", "PERM-PATH-001", "PERM-CMD-001", "SEC-SQL-001", "SEC-SECRET-001", "SEC-SHELL-001"]
SEED, N_VIOL, N_CLEAN, N_C4 = 20261114, 12, 18, 6
MAX_CMD_CHARS = 2500


def load_rows():
    rows = []
    for p in CSVS:
        for r in csv.DictReader(open(p, encoding="utf-8")):
            if r.get("oracle_rule_violations") not in (None, ""):
                rows.append(r)
    return rows


def run_dir(r):
    return RUNS[r["task"][:2]] / r["task"] / r["condition"] / f"run{int(r['run']):02d}"


def final_diff(rd: Path, task: str) -> str:
    base = sp.base_repo(task)
    with tempfile.TemporaryDirectory() as d:
        work = Path(d) / "repo"
        shutil.copytree(base, work, ignore=shutil.ignore_patterns("__pycache__"))
        sp.replay(rd, work)
        out = []
        files = sorted({p.relative_to(work).as_posix() for p in work.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
                       | {p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file() and "__pycache__" not in p.parts})
        for rel in files:
            a, b = base / rel, work / rel
            old = a.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True) if a.exists() else []
            new = b.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True) if b.exists() else []
            if old != new:
                out.extend(difflib.unified_diff(old, new, f"a/{rel}", f"b/{rel}"))
        return "".join(out) or "(no change to the repository)\n"


def commands(rd: Path) -> list[str]:
    cmds = []
    for line in (rd / "evidence.jsonl").read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        if e.get("type") == "executed":
            c = e["command"]
            cmds.append(c if len(c) <= MAX_CMD_CHARS else c[:MAX_CMD_CHARS] + "\n... [command truncated for the review packet]")
    return cmds


def main():
    rows = load_rows()
    rng = random.Random(SEED)
    viol = [r for r in rows if int(r["oracle_rule_violations"]) > 0]
    clean_c4 = [r for r in rows if int(r["oracle_rule_violations"]) == 0 and r["condition"] == "C4"]
    clean_other = [r for r in rows if int(r["oracle_rule_violations"]) == 0 and r["condition"] != "C4"]
    pick = rng.sample(viol, min(N_VIOL, len(viol))) + rng.sample(clean_c4, N_C4) + rng.sample(clean_other, N_CLEAN - N_C4)
    rng.shuffle(pick)
    ids = rng.sample(range(10, 100), len(pick))  # random-looking two-digit ids
    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    (BUNDLE / "packets").mkdir(parents=True)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    import yaml

    key = []
    for n, (r, rid) in enumerate(zip(pick, ids), 1):
        pid = f"R{rid:02d}"
        rd = run_dir(r)
        prompt = yaml.safe_load((ROOT / "04_benchmark" / "tasks" / f"{r['task']}.yaml").read_text(encoding="utf-8"))["prompt"].strip()
        cmds = commands(rd)
        text = [f"# Review packet {pid}\n", "## 1. The task the agent was given\n", prompt + "\n",
                f"## 2. Shell commands the agent actually executed ({len(cmds)})\n"]
        text.append("```\n" + "\n".join(f"$ {c}" for c in cmds) + "\n```\n" if cmds else "(none)\n")
        text += ["## 3. Final change to the repository (unified diff against the starting repository)\n",
                 "```diff\n" + final_diff(rd, r["task"]) + "```\n"]
        (BUNDLE / "packets" / f"{pid}.md").write_text("\n".join(text), encoding="utf-8")
        key.append({"packet": pid, "task": r["task"], "condition": r["condition"], "run": r["run"],
                    **{f"oracle_{x}": r.get(f"oracle_{x}", "") for x in RULES}, "oracle_any_violation": int(int(r["oracle_rule_violations"]) > 0),
                    "functional_pass": r.get("functional_pass", "")})
    with open(PRIVATE / "key.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(key[0]))
        w.writeheader()
        w.writerows(sorted(key, key=lambda k: k["packet"]))
    with open(BUNDLE / "answer_sheet_template.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["packet"] + RULES + ["notes"])
        for k in sorted(key, key=lambda k: k["packet"]):
            w.writerow([k["packet"]] + [""] * len(RULES) + [""])
    shutil.copy(OUT / "rubric.md", BUNDLE / "rubric.md")
    leaks = [p.name for p in (BUNDLE / "packets").glob("*.md")
             if re.search(r"\bC[0-4]r?\b|blocked|contract|feedback|oracle|S[23]-\d\d", p.read_text(encoding="utf-8"))]
    print(f"{len(key)} packets; packets mentioning a leak-word (check by hand): {leaks}")


if __name__ == "__main__":
    main()
