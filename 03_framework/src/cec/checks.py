"""Executable contract checks. Every evaluation returns a four-state CheckResult (decision 0014).

A check that cannot run returns UNKNOWN with a cause; it never silently passes.
"""

import ast
import re
from fnmatch import fnmatch

from .edit_tool import ProposedEdit
from .eku import EKU, check_fresh
from .outcomes import CheckResult, Outcome

# Shell exit codes / messages that mean "the checker itself is missing", not "the rule failed".
_UNAVAILABLE_RC = {126, 127}
_UNAVAILABLE_MARKERS = ("command not found", "No module named", "is not recognized as an internal or external command")


def _result(eku: EKU, outcome: Outcome, target: str, evidence: str = "", cause: str | None = None, stage: str | None = None,
            **extra) -> CheckResult:
    return CheckResult(eku.id, stage or eku.stage, outcome, eku.severity, evidence[:2000], cause, target, extra)


def _stale_guard(eku: EKU, target: str, stage: str | None = None) -> CheckResult | None:
    if not check_fresh(eku):
        return _result(eku, Outcome.UNKNOWN, target, "check spec has no matching evidence_hash", cause="stale_evidence",
                       stage=stage)
    return None


def check_command(ekus: list[EKU], command: str) -> list[CheckResult]:
    """pre_action on a bash command."""
    out = []
    for e in ekus:
        if e.check["kind"] != "command_deny":
            continue
        if r := _stale_guard(e, command):
            out.append(r)
            continue
        hit = next((p for p in e.check["patterns"] if re.search(p, command)), None)
        out.append(_result(e, Outcome.FAIL if hit else Outcome.PASS, command, f"matched /{hit}/" if hit else ""))
    return out


def check_proposed_edit(ekus: list[EKU], edit: ProposedEdit, stage: str | None = None) -> list[CheckResult]:
    """pre_action on a proposed edit (before it is written); with stage="pre_acceptance", on the final diff vs base."""
    out = []
    for e in ekus:
        kind = e.check["kind"]
        if kind not in ("path_deny", "content_deny"):
            continue
        if r := _stale_guard(e, edit.path, stage):
            out.append(r)
            continue
        if kind == "path_deny":
            hit = next((g for g in e.check["globs"] if fnmatch(edit.path, g)), None)
            out.append(_result(e, Outcome.FAIL if hit else Outcome.PASS, edit.path, f"path matches {hit}" if hit else "", stage=stage))
        else:
            if not e.in_scope(edit.path):
                out.append(_result(e, Outcome.NOT_APPLICABLE, edit.path, stage=stage))
                continue
            hits = [(p, l) for l in edit.added_lines for p in e.check["patterns"] if re.search(p, l)]
            ev = "; ".join(f"/{p}/ in: {l.strip()}" for p, l in hits[:3])
            out.append(_result(e, Outcome.FAIL if hits else Outcome.PASS, edit.path, ev, stage=stage))
    return out


def check_file_after_edit(ekus: list[EKU], path: str, content: str, stage: str | None = None) -> list[CheckResult]:
    """post_edit on the file content after an applied edit; with stage="pre_acceptance", on the final file."""
    out = []
    for e in ekus:
        if e.check["kind"] != "import_deny":
            continue
        if r := _stale_guard(e, path, stage):
            out.append(r)
            continue
        if not e.in_scope(path) or not path.endswith(".py"):
            out.append(_result(e, Outcome.NOT_APPLICABLE, path, stage=stage))
            continue
        try:
            tree = ast.parse(content)
        except SyntaxError as exc:
            out.append(_result(e, Outcome.UNKNOWN, path, f"cannot parse: {exc}", cause="inconclusive", stage=stage))
            continue
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imported.append(node.module)
        bad = [m for m in imported for pre in e.check["forbidden_prefixes"] if m == pre or m.startswith(pre + ".")]
        out.append(_result(e, Outcome.FAIL if bad else Outcome.PASS, path, f"forbidden imports: {bad}" if bad else "", stage=stage))
    return out


def check_execution(ekus: list[EKU], command: str, output: dict) -> list[CheckResult]:
    """post_execution on an executed command's output."""
    out = []
    for e in ekus:
        if e.check["kind"] != "output_deny":
            continue
        if not re.search(e.check.get("command_pattern", ".*"), command):
            continue  # this check does not observe this command at all; not recorded
        if r := _stale_guard(e, command):
            out.append(r)
            continue
        if output.get("exception_info"):
            out.append(_result(e, Outcome.UNKNOWN, command, output["exception_info"], cause="checker_error"))
            continue
        text = output.get("output", "")
        hit = next((p for p in e.check["patterns"] if re.search(p, text)), None)
        out.append(_result(e, Outcome.FAIL if hit else Outcome.PASS, command, f"output matched /{hit}/" if hit else ""))
    return out


def check_repository(ekus: list[EKU], run_command) -> list[CheckResult]:
    """pre_acceptance on the repository state. run_command(cmd, timeout) -> mini-style output dict."""
    out = []
    for e in ekus:
        if e.check["kind"] != "repo_command":
            continue
        if r := _stale_guard(e, "repository"):
            out.append(r)
            continue
        res = run_command(e.check["command"], e.check.get("timeout_s", 120))
        text, rc = res.get("output", ""), res.get("returncode")
        if res.get("extra", {}).get("exception_type") == "TimeoutExpired":
            out.append(_result(e, Outcome.UNKNOWN, "repository", text[-1500:], cause="timeout"))
        elif res.get("exception_info"):
            out.append(_result(e, Outcome.UNKNOWN, "repository", res["exception_info"], cause="checker_error"))
        elif rc in _UNAVAILABLE_RC or (rc != 0 and any(m in text for m in _UNAVAILABLE_MARKERS)):
            out.append(_result(e, Outcome.UNKNOWN, "repository", text[-1500:], cause="checker_unavailable"))
        else:
            out.append(_result(e, Outcome.PASS if rc == 0 else Outcome.FAIL, "repository", "" if rc == 0 else text[-1500:]))
    return out
