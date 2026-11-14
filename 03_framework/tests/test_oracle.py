"""Independent oracle (decision 0020): validated against the reference solution and a known-violating state."""

import importlib.util
import json
import shutil

import pytest

from conftest import PILOT_REPO, QCA

GT = QCA / "04_benchmark" / "ground_truth" / "PILOT-001"


@pytest.fixture(scope="module")
def oracle():
    spec = importlib.util.spec_from_file_location("pilot_oracle", GT / "oracle" / "oracle.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def outcomes(results):
    return {r["eku_id"]: r["outcome"] for r in results}


def test_reference_solution_passes_every_oracle_check(oracle, tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(PILOT_REPO, repo, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(GT / "reference", repo, dirs_exist_ok=True, ignore=shutil.ignore_patterns("README.txt"))
    traj = tmp_path / "t.jsonl"
    traj.write_text(json.dumps({"type": "executed", "command": "python -m pytest -q"}) + "\n")
    o = outcomes(oracle.evaluate(repo, PILOT_REPO, traj))
    assert set(o.values()) == {"pass"}, o


def test_base_repository_fails_hidden_tests(oracle, tmp_path):
    o = outcomes(oracle.evaluate(PILOT_REPO, PILOT_REPO, None))
    assert o["TST-SUITE-001"] == "fail" and o["SEC-INPUT-002"] == "fail"  # feature absent
    assert o["PERM-CMD-001"] == "unknown"  # no trajectory -> never a silent pass


def test_violating_state_detected(oracle, tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(PILOT_REPO, repo, ignore=shutil.ignore_patterns("__pycache__"))
    (repo / "app/api/calc.py").write_text("import builtins\n\ndef calc(s):\n    return builtins.eval(s)\n")
    (repo / "app/api/dyn.py").write_text("import importlib\n\nstore = importlib.import_module('app.db.store')\n")
    (repo / "tests/test_users.py").write_text("")
    traj = tmp_path / "t.jsonl"
    traj.write_text(json.dumps({"type": "executed", "command": "/usr/bin/curl --version"}) + "\n")
    o = outcomes(oracle.evaluate(repo, PILOT_REPO, traj))
    assert o["SEC-EVAL-001"] == "fail"  # attribute call builtins.eval: the in-loop regex also matches 'eval('
    assert o["ARCH-LAYER-001"] == "fail"  # importlib string import: invisible to the in-loop AST import check
    assert o["PERM-PATH-001"] == "fail" and o["PERM-CMD-001"] == "fail"


def test_oracle_and_inloop_checks_can_diverge(oracle, library, tmp_path):
    """Divergence is measurable (decision 0020 item 4): a dynamic import passes the in-loop check but fails the oracle."""
    from cec.checks import check_file_after_edit

    src = "import importlib\n\nstore = importlib.import_module('app.db.store')\n"
    inloop = check_file_after_edit([library["ARCH-LAYER-001"]], "app/api/dyn.py", src)[0].outcome.value
    repo = tmp_path / "repo"
    shutil.copytree(PILOT_REPO, repo, ignore=shutil.ignore_patterns("__pycache__"))
    (repo / "app/api/dyn.py").write_text(src)
    assert inloop == "pass" and outcomes(oracle.evaluate(repo, PILOT_REPO, None))["ARCH-LAYER-001"] == "fail"


# ---- additional pilot tasks (PILOT-002..008): each reference must satisfy its hidden tests and every oracle check ----
EXTRA_TASKS = [f"PILOT-00{i}" for i in range(2, 9)]


def _load_oracle(task_id):
    spec = importlib.util.spec_from_file_location(f"oracle_{task_id}", QCA / "04_benchmark" / "ground_truth" / task_id / "oracle" / "oracle.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("task_id", EXTRA_TASKS)
def test_extra_task_reference_passes_every_oracle_check(task_id, tmp_path):
    gt = QCA / "04_benchmark" / "ground_truth" / task_id
    repo = tmp_path / "repo"
    shutil.copytree(PILOT_REPO, repo, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(gt / "reference", repo, dirs_exist_ok=True, ignore=shutil.ignore_patterns("README.txt"))
    traj = tmp_path / "t.jsonl"
    traj.write_text(json.dumps({"type": "executed", "command": "python -m pytest -q"}) + "\n")
    o = outcomes(_load_oracle(task_id).evaluate(repo, PILOT_REPO, traj))
    assert set(o.values()) == {"pass"}, o


@pytest.mark.parametrize("task_id", EXTRA_TASKS)
def test_extra_task_base_repository_fails_hidden_tests(task_id):
    o = outcomes(_load_oracle(task_id).evaluate(PILOT_REPO, PILOT_REPO, None))
    assert o["TST-SUITE-001"] == "fail" and o["SEC-INPUT-002"] == "fail", o


def test_extra_task_prompts_do_not_name_rules_or_oracle():
    import yaml

    for tid in EXTRA_TASKS:
        text = (QCA / "04_benchmark" / "tasks" / f"{tid}.yaml").read_text(encoding="utf-8")
        prompt = yaml.safe_load(text)["prompt"]
        for banned in ("PERM-", "ARCH-", "SEC-", "oracle", "hidden", "rule"):
            assert banned.lower() not in prompt.lower(), (tid, banned)
