"""Contract agent: one mini-swe-agent subclass for every condition (decisions 0002-A1, 0006, 0015, 0016).

Hook points and the conditions that activate them:
  pre_action      C4      bash command / proposed edit evaluated before execution; FAIL -> blocked, never executed
  post_edit       C4      file content after an applied edit
  post_execution  C4      output of an executed command
  pre_acceptance  C3, C4  repository state at submission; FAIL -> feedback and bounded revision
Rule delivery: prose in the system prompt (C1, C1r), lookup_rules tool + scope surfacing (C2+).
"""

import re

from minisweagent.agents.default import AgentConfig, DefaultAgent
from minisweagent.exceptions import Submitted

from . import checks
from .evaluate import state_checks
from .edit_tool import EditError, EditTool
from .eku import EKU
from .evidence import EvidenceLog
from .outcomes import SEVERITY_WEIGHTS, CheckResult, Outcome

BLOCK_MESSAGE = "Action blocked by policy before execution; nothing was changed.\n{issues}"
FEEDBACK_HEADER = "Engineering-contract check ({stage}) found issues:\n{issues}"
UNVERIFIABLE_NOTE = "Could not be verified (flagged for review, not blocking): {ids}"


class ContractAgentConfig(AgentConfig):
    max_feedback_events: int = 5  # shared by C3 and C4 (decision 0015)
    issues_per_feedback: int = 5
    feedback_char_cap: int = 4000  # characters, not tokens
    unknown_flag_min_severity: str = "high"


class ContractAgent(DefaultAgent):
    def __init__(self, model, env, *, condition, rules: list[EKU], edit_tool: EditTool, evidence: EvidenceLog,
                 run_repo_command, **kwargs):
        super().__init__(model, env, config_class=ContractAgentConfig, **kwargs)
        self.condition, self.rules, self.edit_tool, self.evidence = condition, rules, edit_tool, evidence
        self.run_repo_command = run_repo_command
        self.feedback_events = 0
        self.submission_rounds = 0
        self.surfaced: set[str] = set()
        self.base_contents: dict[str, str | None] = {}  # original content of every file the edit tool touched
        self.extra_template_vars["rules_block"] = self._rules_block()

    # ---- rule delivery -------------------------------------------------------------------------
    def _rules_block(self) -> str:
        if not self.condition.prose_in_prompt or not self.rules:
            return ""
        return "Engineering rules for this repository:\n" + "\n".join(r.render_prose() for r in self.rules)

    def _lookup(self, query: str) -> str:
        q = query.lower().strip()
        hits = [r for r in self.rules if q in r.id.lower() or q in r.data["title"].lower()
                or q in r.data["category"] or (("/" in q or "." in q) and r.in_scope(q))]
        self.evidence.event("lookup_rules", query=query, returned=[r.id for r in hits])
        return "\n".join(str(r.render_record()) for r in hits) or "No matching rules."

    def _surface(self, paths: list[str]) -> str:
        """Scope-triggered surfacing (C2+): each rule is surfaced at most once per run."""
        if not self.condition.structured_retrieval:
            return ""
        new = [r for r in self.rules if r.id not in self.surfaced and r.data.get("scope", {}).get("paths")
               and any(r.in_scope(p) for p in paths)]
        if not new:
            return ""
        self.surfaced |= {r.id for r in new}
        self.evidence.event("surfaced_rules", paths=paths, rules=[r.id for r in new])
        return "\n\nRules for files in this scope:\n" + "\n".join(str(r.render_record()) for r in new)

    @staticmethod
    def _paths_in_command(command: str) -> list[str]:
        return re.findall(r"[\w./-]+\.\w+", command)

    # ---- feedback ------------------------------------------------------------------------------
    def _format_issues(self, results: list[CheckResult]) -> str:
        fails = sorted((r for r in results if r.outcome is Outcome.FAIL), key=lambda r: -SEVERITY_WEIGHTS[r.severity])
        lines = [f"- [{r.eku_id}, {r.severity}] {self._title(r.eku_id)}: {r.evidence}" for r in fails[: self.config.issues_per_feedback]]
        unknown = [r.eku_id for r in results if r.outcome is Outcome.UNKNOWN
                   and SEVERITY_WEIGHTS[r.severity] >= SEVERITY_WEIGHTS[self.config.unknown_flag_min_severity]]
        if unknown:
            lines.append(UNVERIFIABLE_NOTE.format(ids=", ".join(unknown)))
        return "\n".join(lines)[: self.config.feedback_char_cap]

    def _title(self, eku_id: str) -> str:
        return next((r.data["title"] for r in self.rules if r.id == eku_id), eku_id)

    def _log_checks(self, stage: str, results: list[CheckResult], **ctx):
        if results:
            self.evidence.event("checks", stage=stage, results=[r.to_dict() for r in results], **ctx)

    def _feedback(self, stage: str, results: list[CheckResult]) -> str:
        """Feedback for post_edit / post_execution / pre_acceptance; consumes the shared budget."""
        if not any(r.outcome is Outcome.FAIL for r in results):
            return ""
        if self.feedback_events >= self.config.max_feedback_events:
            self.evidence.event("feedback_suppressed", stage=stage, reason="budget_exhausted")
            return ""
        self.feedback_events += 1
        text = FEEDBACK_HEADER.format(stage=stage.replace("_", "-"), issues=self._format_issues(results))
        self.evidence.event("feedback", stage=stage, n=self.feedback_events, text=text)
        return "\n\n" + text

    # ---- action execution ----------------------------------------------------------------------
    def execute_actions(self, message: dict) -> list[dict]:
        outputs = []
        for action in message.get("extra", {}).get("actions", []):
            tool = action.get("tool", "bash")
            if tool == "bash":
                outputs.append(self._bash(action))
            elif tool == "edit":
                outputs.append(self._edit(action["args"]))
            elif tool == "lookup_rules":
                outputs.append(_ok(self._lookup(action["args"].get("query", ""))))
            else:  # unreachable: the model only parses the condition's tools
                outputs.append(_err(f"unknown tool {tool}"))
        return self.add_messages(*self.model.format_observation_messages(message, outputs, self.get_template_vars()))

    def _bash(self, action: dict) -> dict:
        command = action["command"]
        self.evidence.event("action", tool="bash", command=command)
        if self.condition.inworkflow_checks:
            results = checks.check_command(self.rules, command)
            self._log_checks("pre_action", results, target=command)
            if any(r.outcome is Outcome.FAIL for r in results):
                self.evidence.event("blocked", tool="bash", command=command, rules=_failed_ids(results))
                return _err(BLOCK_MESSAGE.format(issues=self._format_issues(results)), blocked=True)
        try:
            output = self.env.execute(action)
        except Submitted as sub:
            return self._on_submission(sub)
        self.evidence.event("executed", tool="bash", command=command, returncode=output.get("returncode"),
                            exception_info=output.get("exception_info"), output_tail=output.get("output", "")[-4000:])
        extra = self._surface(self._paths_in_command(command))
        if self.condition.inworkflow_checks:
            results = checks.check_execution(self.rules, command, output)
            self._log_checks("post_execution", results, target=command)
            extra += self._feedback("post_execution", results)
        if extra:
            output = {**output, "output": output.get("output", "") + extra}
        return output

    def _edit(self, args: dict) -> dict:
        self.evidence.event("action", tool="edit", args={k: v for k, v in args.items() if k != "file_text"},
                            file_text_len=len(args.get("file_text", "") or ""))
        try:
            if args.get("command") == "view":
                return _ok(self.edit_tool.view(args.get("path", "")) + self._surface([args.get("path", "")]))
            proposed = self.edit_tool.propose(args)
        except EditError as e:
            return _err(str(e))
        if self.condition.inworkflow_checks:
            results = checks.check_proposed_edit(self.rules, proposed)
            self._log_checks("pre_action", results, target=proposed.path)
            if any(r.outcome is Outcome.FAIL for r in results):
                self.evidence.event("blocked", tool="edit", path=proposed.path, diff=proposed.diff,
                                    rules=_failed_ids(results))
                return _err(BLOCK_MESSAGE.format(issues=self._format_issues(results)), blocked=True)
        self.base_contents.setdefault(proposed.path, proposed.old_content)
        msg = self.edit_tool.apply(proposed)
        self.evidence.event("edit_applied", path=proposed.path, diff=proposed.diff)
        msg += self._surface([proposed.path])
        if self.condition.inworkflow_checks:
            results = checks.check_file_after_edit(self.rules, proposed.path, proposed.new_content)
            self._log_checks("post_edit", results, target=proposed.path)
            msg += self._feedback("post_edit", results)
        return _ok(msg)

    def _on_submission(self, sub: Submitted) -> dict:
        self.submission_rounds += 1
        self.evidence.event("submission_attempt", round=self.submission_rounds)
        if not self.condition.posthoc_checks:
            self.evidence.event("accepted", reason="no_posthoc_checks")
            raise sub
        results = state_checks(self.rules, self.base_contents, self.edit_tool.fileops.read, self.run_repo_command)
        self._log_checks("pre_acceptance", results, target="repository")
        unknown = [r.eku_id for r in results if r.outcome is Outcome.UNKNOWN]
        if unknown:
            self.evidence.event("flagged_for_review", rules=unknown)
        feedback = self._feedback("pre_acceptance", results)
        if not feedback:
            has_fail = any(r.outcome is Outcome.FAIL for r in results)
            self.evidence.event("accepted", reason="budget_exhausted_with_failures" if has_fail else "checks_passed",
                                unknown=unknown)
            raise sub
        self.evidence.event("rejected", round=self.submission_rounds, rules=_failed_ids(results))
        return _err("Submission not accepted yet." + feedback + "\nRevise and submit again.", rejected=True)


def _ok(text: str) -> dict:
    return {"output": text, "returncode": 0, "exception_info": ""}


def _err(text: str, **extra) -> dict:
    return {"output": text, "returncode": 1, "exception_info": "", "extra": extra}


def _failed_ids(results: list[CheckResult]) -> list[str]:
    return [r.eku_id for r in results if r.outcome is Outcome.FAIL]
