"""Condition flags for the ladder C0-C4 (decision 0006). The same agent code runs every condition."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Condition:
    name: str
    rule_source: str  # "none" | "applicable" | "irrelevant"
    prose_in_prompt: bool  # C1, C1r
    structured_retrieval: bool  # C2+: lookup_rules tool + scope-triggered surfacing
    posthoc_checks: bool  # C3+: checks at submission, bounded revision
    inworkflow_checks: bool  # C4: pre-action blocking, post-edit, post-execution feedback

    def to_dict(self) -> dict:
        return asdict(self)


CONDITIONS = {
    "C0": Condition("C0", "none", False, False, False, False),
    "C1": Condition("C1", "applicable", True, False, False, False),
    "C1r": Condition("C1r", "irrelevant", True, False, False, False),
    "C2": Condition("C2", "applicable", False, True, False, False),
    "C3": Condition("C3", "applicable", False, True, True, False),
    "C4": Condition("C4", "applicable", False, True, True, True),
}
