"""Batch driver for the variance pilot: every (task, condition, run) cell, run-index-major, with parallel workers.

Usage (from 03_framework/, venv python; keys only via the environment, never written to disk):
    GEMINI_KEYS=key1,key2,key3 .venv/Scripts/python ../05_experiments/pilot/run_pilot.py \
        --out ../05_experiments/pilot/pilot_v1 --runs 1-5 --workers 6

Order: all cells of run 1 (shuffled with a fixed seed so no condition is systematically run at a different time),
then run 2, and so on, so the first rounds can be inspected before the rest is spent. Resumable: cells that already
have a termination event are skipped. A run that ends in infrastructure failure is moved to <out>/_infra_failed/
(kept, never analysed as a result, decision 0010) and the cell is retried; quota/auth errors rotate to the next key.
"""

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FW = ROOT / "03_framework"
CONDITIONS = ["C0", "C1", "C1r", "C2", "C3", "C4"]
KEY_ERRORS = re.compile(r"429|RESOURCE_EXHAUSTED|quota|rate.?limit|API key|PERMISSION_DENIED|UNAUTHENTICATED|\b403\b", re.I)

lock = threading.Lock()
state = {"keys": [], "dead": set(), "cool": {}, "rr": 0, "done": 0, "total": 0}


def log(out: Path, msg: str):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    with lock:
        print(line, flush=True)
        with open(out / "driver.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")


def terminated(run_dir: Path):
    ev = run_dir / "evidence.jsonl"
    if not ev.exists():
        return None
    for line in ev.read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        if e.get("type") == "termination":
            return e
    return None


def spent(out: Path) -> float:
    """Total recorded model cost of all finished runs under `out` (USD)."""
    total = 0.0
    for ev in out.glob("*/*/run*/evidence.jsonl"):
        t = terminated(ev.parent)
        if t:
            total += t.get("cost") or 0.0
    return total


def next_key():
    """Round-robin over keys that are neither dead (daily quota) nor cooling down (per-minute quota)."""
    while True:
        with lock:
            alive = [i for i in range(len(state["keys"])) if i not in state["dead"]]
            if not alive:
                return None, None
            now = time.time()
            ready = [i for i in alive if state["cool"].get(i, 0) <= now]
            if ready:
                state["rr"] += 1
                i = ready[state["rr"] % len(ready)]
                return i, state["keys"][i]
            wait = min(state["cool"][i] for i in alive) - now
        time.sleep(max(wait, 1))


def key_failed(idx: int, msg: str, out: Path):
    """Per-day quota (limit: 500 requests) and auth errors retire a key; the per-minute quota (limit: 15) only pauses it."""
    if re.search(r"PerDay|per.?day|limit: (500|1000|1500|2000)|API key not valid|PERMISSION_DENIED|UNAUTHENTICATED", msg, re.I):
        with lock:
            state["dead"].add(idx)
        log(out, f"key #{idx + 1} retired ({msg[:80]!r})")
    else:
        with lock:
            n = state.setdefault("fails", {}).get(idx, 0) + 1
            state["fails"][idx] = n
            wait = min(70 * 2 ** (n - 1), 3600)  # escalates while the key keeps failing (e.g. an unrecognised daily cap)
            state["cool"][idx] = time.time() + wait
        log(out, f"key #{idx + 1} cooling down {wait} s (rate limit, consecutive failure {n})")


IMAGES = {"pilot_repo": "cec-pilot:0.1", "pilot_repo2": "cec-pilot2:0.1", "study2_repo": "cec-study2:0.1"}


def image_for(task: str) -> str:
    import yaml

    repo = yaml.safe_load((ROOT / "04_benchmark" / "tasks" / f"{task}.yaml").read_text(encoding="utf-8"))["repository"]
    return IMAGES[repo]


def run_cell(cell, args, out: Path):
    task, cond, run = cell
    run_dir = out / task / cond / f"run{run:02d}"
    if terminated(run_dir) and terminated(run_dir)["termination_class"] != "infra_failure":
        return "skipped"
    if args.budget is not None and spent(out) + args.workers * 0.04 > args.budget:
        return "budget"
    for attempt in range(1, 5):
        idx, key = next_key()
        if key is None:
            return "no_keys"
        if run_dir.exists():
            dest = out / "_infra_failed" / f"{task}_{cond}_run{run:02d}_{int(time.time())}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(run_dir), str(dest))
        env = {**os.environ, "GEMINI_API_KEY": key, "OPENROUTER_API_KEY": key, "PYTHONPATH": str(FW / "src"), "MSWEA_SILENT_STARTUP": "1"}
        t0 = time.time()
        subprocess.run([sys.executable, "-m", "cec.run", "--task", str(ROOT / "04_benchmark" / "tasks" / f"{task}.yaml"),
                        "--condition", cond, "--run", str(run), "--out", str(out), "--image", image_for(task), "--config", str(FW / "configs" / args.config)],
                       cwd=FW, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        term = terminated(run_dir)
        if term and term["termination_class"] != "infra_failure":
            with lock:
                state["done"] += 1
                n = state["done"]
                state.setdefault("fails", {})[idx] = 0
            log(out, f"[{n}/{state['total']}] {task} {cond} run{run} -> {term['termination_class']} "
                     f"calls={term['n_calls']} cost=${term.get('cost') or 0:.4f} t={time.time() - t0:.0f}s key#{idx + 1}")
            return "ok"
        msg = ""
        ev = run_dir / "evidence.jsonl"
        if ev.exists():
            for line in ev.read_text(encoding="utf-8").splitlines():
                e = json.loads(line)
                if e.get("type") == "infra_error":
                    msg = e.get("message", "")
        log(out, f"{task} {cond} run{run} attempt {attempt}: infra failure ({msg[:120]!r})")
        if KEY_ERRORS.search(msg):
            key_failed(idx, msg, out)
        time.sleep(5)
    return "failed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--runs", default="1-5")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--config", default="pilot_gemini.yaml")
    ap.add_argument("--budget", type=float, default=None, help="stop starting new runs once recorded cost (plus a margin for runs in flight) would exceed this many USD")
    ap.add_argument("--tasks", default="PILOT-001,PILOT-002,PILOT-003,PILOT-004,PILOT-005,PILOT-006,PILOT-007,PILOT-008")  # phase 2: PILOT2-001,PILOT2-002,PILOT2-003
    ap.add_argument("--conditions", default=",".join(CONDITIONS))
    args = ap.parse_args()
    a, b = (args.runs.split("-") + [args.runs])[:2]
    runs = list(range(int(a), int(b) + 1))
    state["keys"] = [k for k in os.environ["GEMINI_KEYS"].split(",") if k]
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20261112)
    cells = []
    for r in runs:
        block = [(t, c, r) for t in args.tasks.split(",") for c in args.conditions.split(",")]
        rng.shuffle(block)
        cells += block
    state["total"] = len(cells)
    log(out, f"{len(cells)} cells, {args.workers} workers, {len(state['keys'])} key(s)")
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(lambda c: run_cell(c, args, out), cells))
    summary = {k: results.count(k) for k in set(results)}
    log(out, f"finished: {summary}")


if __name__ == "__main__":
    main()
