"""Deterministic applicability predicate (scope + trigger vs task context).

Used for the C1r inapplicability check (decision 0006) and as the seed of the contextual selector.
The pilot freezes R(task) by hand; this predicate must agree with that freeze (tested).
"""

import fnmatch
from dataclasses import dataclass, field

from .eku import EKU


@dataclass
class TaskContext:
    languages: set[str]
    frameworks: set[str]
    task_type: str
    files: list[str] = field(default_factory=list)


def applicable(rule: EKU, ctx: TaskContext) -> tuple[bool, str]:
    scope, trigger = rule.data.get("scope", {}), rule.data.get("trigger", {})
    langs = set(scope.get("languages") or [])
    if langs and "any" not in langs and not langs & ctx.languages:
        return False, f"language {sorted(langs)} not in {sorted(ctx.languages)}"
    fws = set(scope.get("frameworks") or [])
    if fws and not fws & ctx.frameworks:
        return False, f"framework {sorted(fws)} not present"
    types = set(trigger.get("task_types") or [])
    if types and ctx.task_type not in types:
        return False, f"task type {ctx.task_type} not in {sorted(types)}"
    paths = scope.get("paths") or []
    if paths and not any(fnmatch.fnmatch(f, g) for f in ctx.files for g in paths):
        return False, f"no repository file matches {paths}"
    return True, "scope and trigger match"
