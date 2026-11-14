import os
import shutil
import sys
import time
from pathlib import Path

import pytest
import yaml

os.environ.setdefault("MSWEA_SILENT_STARTUP", "1")
os.environ["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", "")  # checker commands use the venv
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from minisweagent.environments.local import LocalEnvironment  # noqa: E402
from minisweagent.models.utils.actions_toolcall import format_toolcall_observation_messages  # noqa: E402

from cec.eku import EKU, load_library  # noqa: E402

QCA = Path(__file__).resolve().parents[2]
RULES_DIR, SCHEMA = QCA / "02_ekus" / "rules", QCA / "02_ekus" / "schema" / "eku.schema.json"
PILOT_REPO = QCA / "04_benchmark" / "repositories" / "pilot_repo"
PILOT_TASK = QCA / "04_benchmark" / "tasks" / "PILOT-001.yaml"
CONFIG = QCA / "03_framework" / "configs" / "pilot.yaml"


@pytest.fixture(scope="session")
def raw_library():
    return load_library(RULES_DIR, SCHEMA)


@pytest.fixture(scope="session")
def library(raw_library):
    """Library with evidence_hash stamped in memory, as if validation had passed (stamping itself is tested separately)."""
    return {k: EKU({**v.data, "evidence_hash": v.spec_hash}) for k, v in raw_library.items()}


@pytest.fixture(scope="session")
def task():
    return yaml.safe_load(PILOT_TASK.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


@pytest.fixture
def repo(tmp_path):
    dst = tmp_path / "repo"
    shutil.copytree(PILOT_REPO, dst, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    return dst


def local_runner(repo: Path):
    env = LocalEnvironment(cwd=str(repo), timeout=120, env={"PYTHONDONTWRITEBYTECODE": "1"})
    return env, (lambda cmd, timeout: env.execute({"command": cmd}, timeout=timeout))


class ScriptedModel:
    """Replays a fixed list of tool calls; skips calls to tools the condition does not offer (a real model cannot call them)."""

    def __init__(self, script: list[dict], tool_names: set[str]):
        self.script = [a for a in script if a["tool"] in tool_names or (a["tool"] == "edit" and "str_replace" in tool_names)]
        self.i = 0
        self.config = type("Cfg", (), {"model_dump": lambda self, **k: {"model_name": "scripted"}})()

    def query(self, messages, **kwargs):
        if self.i < len(self.script):
            a = self.script[self.i]
        else:
            a = {"tool": "bash", "args": {"command": "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"}}
        self.i += 1
        action = {"tool": a["tool"], "args": a["args"], "command": a["args"].get("command", ""), "tool_call_id": f"call_{self.i}"}
        return {"role": "assistant", "content": f"step {self.i}", "extra": {"actions": [action], "cost": 0.0,
                "usage": {"input_tokens": None, "output_tokens": None, "usage_missing": True}, "timestamp": time.time()}}

    def format_message(self, **kwargs):
        return kwargs

    def format_observation_messages(self, message, outputs, template_vars=None):
        return format_toolcall_observation_messages(
            actions=message["extra"]["actions"], outputs=outputs, template_vars=template_vars,
            observation_template="<returncode>{{output.returncode}}</returncode>\n<output>\n{{output.output}}</output>")

    def get_template_vars(self, **kwargs):
        return {}

    def serialize(self):
        return {"info": {"config": {"model": {"model_name": "scripted"}}}}
