"""Build and run one (task, condition, run) under identical infrastructure.

Usage (real pilot; needs Docker and the model's API key in the environment):
    python -m cec.run --task ../04_benchmark/tasks/PILOT-001.yaml --condition C4 --run 1 --out ../05_experiments/pilot/runs
"""

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import yaml
from minisweagent import __version__ as MINI_VERSION
from minisweagent.environments.docker import DockerEnvironment

from .agent import ContractAgent
from .conditions import CONDITIONS
from .edit_tool import DockerFileOps, EditTool
from .eku import load_library
from .evaluate import final_evaluation
from .evidence import EvidenceLog, sha256_file, sha256_obj

ROOT = Path(__file__).resolve().parents[3]  # QCA/
RULES_DIR = ROOT / "02_ekus" / "rules"
SCHEMA = ROOT / "02_ekus" / "schema" / "eku.schema.json"
CONFIG = ROOT / "03_framework" / "configs" / "pilot.yaml"


class ContractDockerEnvironment(DockerEnvironment):
    """Agent bash runs as the unprivileged `agent` user, which has read-only access to /repo (sandbox/Dockerfile).

    The edit tool (DockerFileOps, as root) is therefore the only write path to the repository in every condition.
    Checker commands (run_repo_command) also run as `agent`, so checks cannot modify the repository either.
    """

    def execute(self, action, cwd="", *, timeout=None):
        command = action.get("command", "")
        cmd = [self.config.executable, "exec", "-u", "agent", "-w", cwd or self.config.cwd]
        for key, value in self.config.env.items():
            cmd.extend(["-e", f"{key}={value}"])
        cmd.extend([self.container_id, *self.config.interpreter, command])
        try:
            r = subprocess.run(cmd, text=True, timeout=timeout or self.config.timeout, encoding="utf-8",
                               errors="replace", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output = {"output": r.stdout, "returncode": r.returncode, "exception_info": ""}
        except Exception as e:
            raw = getattr(e, "output", None)
            raw = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else (raw or "")
            output = {"output": raw, "returncode": -1, "exception_info": f"An error occurred while executing the command: {e}",
                      "extra": {"exception_type": type(e).__name__, "exception": str(e)}}
        self._check_finished(output)
        return output

    def cleanup(self):
        """mini-swe-agent's cleanup uses POSIX shell syntax and silently fails on Windows (leaked containers).
        Remove the container directly instead."""
        cid = getattr(self, "container_id", None)
        if cid is not None:
            subprocess.run([self.config.executable, "rm", "-f", cid], capture_output=True, timeout=60)
            self.container_id = None

    def __del__(self):
        self.cleanup()


def rules_for(task: dict, condition, library: dict) -> list:
    rs = task["rule_set"]
    ids = {"none": [], "applicable": rs["applicable"], "irrelevant": rs["irrelevant_control"]["rules"]}[condition.rule_source]
    return [library[i] for i in ids]


def build_agent(*, task: dict, condition, model, env, fileops, run_repo_command, evidence: EvidenceLog,
                library: dict, agent_config: dict) -> ContractAgent:
    return ContractAgent(model, env, condition=condition, rules=rules_for(task, condition, library),
                         edit_tool=EditTool(fileops), evidence=evidence, run_repo_command=run_repo_command,
                         **agent_config)


def manifest(task: dict, condition, rules: list, agent_config: dict, model_config: dict, extra: dict) -> dict:
    return {
        "task_id": task["task_id"], "condition": condition.to_dict(),
        "rules": [{"id": r.id, "version": r.data["version"], "spec_hash": r.spec_hash} for r in rules],
        "mini_version": MINI_VERSION, "python": sys.version, "platform": platform.platform(),
        "agent_config_hash": sha256_obj(agent_config), "model_config": model_config,
        "contract_layer_hash": sha256_obj({p.name: sha256_file(p) for p in sorted(Path(__file__).parent.glob("*.py"))}),
        "rules_library_hash": sha256_obj({p.name: sha256_file(p) for p in sorted(RULES_DIR.rglob("*.yaml"))}),
        **extra,
    }


def classify(exit_status, error) -> str:
    """Coarse termination class. timeout/early_stop/wrong_solution (decision 0016) are derived in analysis."""
    if error is not None:
        return "infra_failure"
    return {"Submitted": "submitted", "LimitsExceeded": "limits", "TimeExceeded": "limits",
            "RepeatedFormatError": "format_failure"}.get(exit_status, "infra_failure")


def repetition_stats(messages) -> dict:
    """Repeated identical actions: the basis of the retry-until-timeout metric (decision 0009)."""
    sigs = [json.dumps([a.get("tool"), a.get("args")], sort_keys=True, default=str)
            for m in messages if m.get("role") == "assistant" for a in m.get("extra", {}).get("actions", [])]
    longest = cur = 0
    for i, s in enumerate(sigs):
        cur = cur + 1 if i and s == sigs[i - 1] else 1
        longest = max(longest, cur)
    counts = {}
    for s in sigs:
        counts[s] = counts.get(s, 0) + 1
    return {"n_actions": len(sigs), "max_identical_total": max(counts.values(), default=0), "max_identical_consecutive": longest}


def main(argv=None):  # pragma: no cover - requires Docker and API access; exercised in the smoke test
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, type=Path)
    ap.add_argument("--condition", required=True, choices=sorted(CONDITIONS))
    ap.add_argument("--run", required=True, type=int)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--image", default="cec-pilot:0.1")
    ap.add_argument("--config", type=Path, default=CONFIG)
    args = ap.parse_args(argv)

    from .model import ContractModel

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    task = yaml.safe_load(args.task.read_text(encoding="utf-8"))
    condition = CONDITIONS[args.condition]
    library = load_library(RULES_DIR, SCHEMA)
    run_dir = args.out / task["task_id"] / condition.name / f"run{args.run:02d}"
    if run_dir.exists():
        sys.exit(f"refusing to overwrite existing run directory {run_dir}")
    run_dir.mkdir(parents=True)
    evidence = EvidenceLog(run_dir / "evidence.jsonl")

    env = ContractDockerEnvironment(image=args.image, cwd="/repo", **cfg["environment"])
    fileops = DockerFileOps(env.container_id, "/repo")

    def run_repo_command(cmd, timeout):
        return env.execute({"command": cmd}, timeout=timeout)

    model_cfg = {**cfg["model"], "model_kwargs": {**cfg["model"]["model_kwargs"],
                                                  "seed": cfg["model"]["model_kwargs"]["seed"] + args.run}}
    model = ContractModel(condition=condition, **model_cfg)
    agent = build_agent(task=task, condition=condition, model=model, env=env, fileops=fileops,
                        run_repo_command=run_repo_command, evidence=evidence, library=library,
                        agent_config={**cfg["agent"], "output_path": run_dir / "trajectory.json"})
    image_digest = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", args.image],
                                  capture_output=True, text=True).stdout.strip()
    evidence.event("manifest", **manifest(task, condition, agent.rules, cfg["agent"], model_cfg,
                                          {"image": args.image, "image_digest": image_digest, "run": args.run}))
    t0 = time.time()
    info, error = {}, None
    try:
        info = agent.run(task["prompt"])
    except Exception as e:  # noqa: BLE001 - infrastructure failures are logged and classified, never dropped (0010)
        error = e
        evidence.event("infra_error", error_type=type(e).__name__, message=str(e)[:500])
    exit_status = agent.messages[-1].get("extra", {}).get("exit_status") if agent.messages else None
    evidence.event("termination", exit_status=exit_status, termination_class=classify(exit_status, error),
                   wall_clock_s=time.time() - t0, n_calls=agent.n_calls, cost=agent.cost,
                   feedback_events=agent.feedback_events, submission_rounds=agent.submission_rounds,
                   repetition=repetition_stats(agent.messages))
    try:
        if error is None:
            full_rules = rules_for(task, CONDITIONS["C4"], library)  # evaluation always uses the applicable set
            result = final_evaluation(full_rules, evidence.read(), agent.base_contents, fileops.read, run_repo_command)
            (run_dir / "final_evaluation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    finally:
        env.cleanup()
    if error is not None:
        sys.exit(f"infrastructure failure ({type(error).__name__}); see {run_dir}/evidence.jsonl")
    return info


if __name__ == "__main__":
    main()
