"""Four-state contract outcomes (decision 0014)."""

from dataclasses import asdict, dataclass, field
from enum import Enum


class Outcome(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


UNKNOWN_CAUSES = {
    "checker_unavailable",
    "checker_error",
    "timeout",
    "stale_evidence",
    "inconclusive",
    "truncated_trace",
}

STAGES = ("pre_action", "post_edit", "post_execution", "pre_acceptance")

SEVERITY_WEIGHTS = {"low": 1, "medium": 2, "high": 4, "critical": 8}  # provisional, decision 0007


@dataclass
class CheckResult:
    eku_id: str
    stage: str
    outcome: Outcome
    severity: str
    evidence: str = ""
    cause: str | None = None
    target: str = ""  # command, file path, or "repository"
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.stage not in STAGES:
            raise ValueError(f"unknown stage {self.stage!r}")
        if self.outcome is Outcome.UNKNOWN and self.cause not in UNKNOWN_CAUSES:
            raise ValueError(f"unknown outcome requires a cause in {sorted(UNKNOWN_CAUSES)}, got {self.cause!r}")
        if self.outcome is not Outcome.UNKNOWN and self.cause is not None:
            raise ValueError("cause is only allowed for unknown outcomes")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["outcome"] = self.outcome.value
        return d


def compliance(results: list[CheckResult]) -> dict:
    """pass / (pass + fail); not_applicable excluded; unknown reported separately and as a fail-sensitivity variant."""
    n = {o: sum(r.outcome is o for r in results) for o in Outcome}
    evaluable = n[Outcome.PASS] + n[Outcome.FAIL]
    with_unknown = evaluable + n[Outcome.UNKNOWN]
    return {
        "n_pass": n[Outcome.PASS],
        "n_fail": n[Outcome.FAIL],
        "n_unknown": n[Outcome.UNKNOWN],
        "n_not_applicable": n[Outcome.NOT_APPLICABLE],
        "compliance": n[Outcome.PASS] / evaluable if evaluable else None,
        "compliance_unknown_as_fail": n[Outcome.PASS] / with_unknown if with_unknown else None,
        "severity_weighted_violations": sum(
            SEVERITY_WEIGHTS[r.severity] for r in results if r.outcome is Outcome.FAIL
        ),
    }
