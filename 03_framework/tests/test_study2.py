"""Study 2 fixture (study2_repo) and tasks S2-01..S2-14: every reference passes every oracle check, the base fails the hidden
tests, prompts do not name rules or methods, the fixture text does not reveal rules, rule spread meets the plan."""

import importlib.util
import json
import shutil
from collections import Counter

import pytest
import yaml

from cec import checks
from cec.outcomes import Outcome
from conftest import QCA, local_runner

REPO3 = QCA / "04_benchmark" / "repositories" / "study2_repo"
GT = QCA / "04_benchmark" / "ground_truth"
TASKS = [f"S2-{i:02d}" for i in range(1, 15)]
ALL_CHECKS = {"ARCH-LAYER-001", "SEC-EVAL-001", "PERM-PATH-001", "PERM-CMD-001", "TST-SUITE-001", "SEC-INPUT-002",
              "STY-LINT-001", "SEC-SQL-001", "SEC-SECRET-001", "SEC-SHELL-001"}


def _task(tid):
    return yaml.safe_load((QCA / "04_benchmark" / "tasks" / f"{tid}.yaml").read_text(encoding="utf-8"))


def _oracle(tid):
    spec = importlib.util.spec_from_file_location(f"oracle_{tid}", GT / tid / "oracle" / "oracle.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _outcomes(results):
    return {r["eku_id"]: r["outcome"] for r in results}


@pytest.mark.parametrize("tid", TASKS)
def test_reference_passes_every_oracle_check(tid, tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(REPO3, repo, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(GT / tid / "reference", repo, dirs_exist_ok=True, ignore=shutil.ignore_patterns("README.txt"))
    traj = tmp_path / "t.jsonl"
    traj.write_text(json.dumps({"type": "executed", "command": "python -m pytest -q"}) + "\n")
    o = _outcomes(_oracle(tid).evaluate(repo, REPO3, traj))
    assert set(o) == ALL_CHECKS and set(o.values()) == {"pass"}, o


@pytest.mark.parametrize("tid", TASKS)
def test_base_repository_fails_hidden_tests(tid):
    o = _outcomes(_oracle(tid).evaluate(REPO3, REPO3, None))
    assert o["TST-SUITE-001"] == "fail" and o["SEC-INPUT-002"] == "fail", o


def test_base_repository_passes_its_own_checks(library):
    _, run = local_runner(REPO3)
    res = {r.eku_id: r for r in checks.check_repository([library[i] for i in ("TST-SUITE-001", "STY-LINT-001")], run)}
    assert res["TST-SUITE-001"].outcome is Outcome.PASS and res["STY-LINT-001"].outcome is Outcome.PASS


def test_fixture_text_does_not_reveal_rules():
    banned = ("layer", "must not", "never", "only app.services", "forbidden", "do not", "untrusted", "inject", "secret")
    for f in REPO3.rglob("*.py"):
        text = f.read_text(encoding="utf-8").lower()
        assert not any(b in text for b in banned), (f.name, [b for b in banned if b in text])


@pytest.mark.parametrize("tid", TASKS)
def test_task_prompt_does_not_name_rules_or_methods(tid):
    prompt = _task(tid)["prompt"].lower()
    for banned in ("sec-", "perm-", "arch-", "oracle", "hidden", "inject", "parameteri", "hard-code", "shell", "eval(", "ast.",
                   "literal_eval", "subprocess", "pip ", "install", "layer", "protected", "do not modify"):
        assert banned not in prompt, (tid, banned)


def test_rule_spread_meets_plan():
    tasks = [_task(t) for t in TASKS]
    assert len(tasks) >= 12
    count = Counter(t["tempted_rule"] for t in tasks)
    assert len(count) >= 7 and min(count.values()) >= 2 and max(count.values()) <= 0.25 * len(tasks), count
    assert sum(1 for t in tasks if "test suite" in t["prompt"]) <= 4  # rule/task-tension stratum


@pytest.mark.parametrize("tid", TASKS)
def test_irrelevant_control_is_inapplicable(tid, library):
    from cec.selector import TaskContext, applicable

    files = [p.relative_to(REPO3).as_posix() for p in REPO3.rglob("*") if p.is_file()]
    ctx = TaskContext(languages={"python"}, frameworks=set(), task_type="feature", files=files)
    rs = _task(tid)["rule_set"]
    for rid in rs["irrelevant_control"]["rules"]:
        assert not applicable(library[rid], ctx)[0], (tid, rid)
    for rid in rs["applicable"]:
        assert applicable(library[rid], ctx)[0], (tid, rid)
