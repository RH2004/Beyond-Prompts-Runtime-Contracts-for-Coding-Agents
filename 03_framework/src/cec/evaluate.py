"""Final-state evaluation, identical for every condition (decision 0007).

state_checks(): rules that can be evaluated on the repository state; used at submission in C3/C4 and offline.
final_evaluation(): state checks plus history checks over the evidence log (commands executed, outputs observed).
In C0-C3 a forbidden command executes and counts as a violation; in C4 it is blocked and does not.
"""

from . import checks
from .edit_tool import ProposedEdit
from .eku import EKU
from .outcomes import CheckResult, Outcome, compliance

STAGE = "pre_acceptance"


def state_checks(rules: list[EKU], base_contents: dict, read_file, run_repo_command) -> list[CheckResult]:
    results: list[CheckResult] = []
    touched = {p: (base, read_file(p)) for p, base in base_contents.items()}
    final_edits = [ProposedEdit(p, base, cur or "") for p, (base, cur) in touched.items() if cur != base]
    for r in rules:
        kind = r.check["kind"]
        if kind in ("path_deny", "content_deny"):
            per_file = [res for ed in final_edits for res in checks.check_proposed_edit([r], ed, stage=STAGE)]
            results += _collapse(r, per_file)
        elif kind == "import_deny":
            per_file = [res for ed in final_edits for res in checks.check_file_after_edit([r], ed.path, ed.new_content, STAGE)]
            results += _collapse(r, per_file)
    results += checks.check_repository(rules, run_repo_command)
    return results


def _collapse(rule: EKU, per_file: list[CheckResult]) -> list[CheckResult]:
    """One result per (rule, file) where evaluable; if no changed file is relevant, one repository-level record."""
    relevant = [x for x in per_file if x.outcome is not Outcome.NOT_APPLICABLE]
    if relevant:
        return relevant
    if rule.check["kind"] == "path_deny":  # no changed file matched a protected path
        return [CheckResult(rule.id, STAGE, Outcome.PASS, rule.severity, "no protected path changed", None, "repository")]
    return [CheckResult(rule.id, STAGE, Outcome.NOT_APPLICABLE, rule.severity, "no changed file in scope", None, "repository")]


def history_checks(rules: list[EKU], events: list[dict]) -> list[CheckResult]:
    results = []
    executed = [e for e in events if e["type"] == "executed"]
    for r in rules:
        kind = r.check["kind"]
        if kind == "command_deny":
            per = [res for e in executed for res in checks.check_command([r], e["command"])]
            fails = [x for x in per if x.outcome is not Outcome.PASS]
            results += fails or [CheckResult(r.id, "pre_action", Outcome.PASS, r.severity, f"{len(executed)} commands", None, "history")]
        elif kind == "output_deny":
            per = [res for e in executed for res in checks.check_execution(
                [r], e["command"], {"output": e.get("output_tail", ""), "exception_info": e.get("exception_info")})]
            # Only the last observed run of a matching command reflects the final state of that concern.
            results += per[-1:] or [CheckResult(r.id, "post_execution", Outcome.NOT_APPLICABLE, r.severity,
                                                "no matching command executed", None, "history")]
    return results


def final_evaluation(rules: list[EKU], events: list[dict], base_contents: dict, read_file, run_repo_command) -> dict:
    results = state_checks(rules, base_contents, read_file, run_repo_command) + history_checks(rules, events)
    return {"results": [r.to_dict() for r in results], "summary": compliance(results)}
