"""Stamp evidence_hash into EKU files, only after the rule-validation tests pass (decision 0014 freshness).

Usage (from 03_framework/):  python -m cec.stamp
Any later change to a rule's check spec changes its hash, so the rule evaluates to unknown(stale_evidence)
until it is re-validated and re-stamped. Every stamp is appended to 02_ekus/stamp_log.jsonl.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

from .eku import EKU
from .run import RULES_DIR, ROOT

VALIDATION_TESTS = [
    "tests/test_core.py::test_each_applicable_rule_has_pass_and_fail_example",
    "tests/test_core.py::test_irrelevant_rules_inapplicable",
    "tests/test_core.py::test_applicable_rules_agree_with_manual_freeze",
    "tests/test_core.py::test_library_validates",
    "tests/test_phase2.py::test_each_new_rule_has_pass_and_fail_examples",
    "tests/test_phase2.py::test_new_rules_do_not_apply_outside_app",
    "tests/test_phase2.py::test_irrelevant_control_is_inapplicable_to_fixture_2",
]


def main():
    fw = ROOT / "03_framework"
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *VALIDATION_TESTS], cwd=fw)
    if r.returncode != 0:
        sys.exit("validation tests failed; nothing stamped")
    log = ROOT / "02_ekus" / "stamp_log.jsonl"
    stamped = []
    for path in sorted(RULES_DIR.rglob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        header = "".join(l for l in text.splitlines(keepends=True) if l.startswith("#"))
        data = yaml.safe_load(text)
        h = EKU(data).spec_hash
        if data.get("evidence_hash") == h:
            continue
        data["evidence_hash"] = h
        path.write_text(header + yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
        stamped.append({"id": data["id"], "version": data["version"], "evidence_hash": h})
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "validated_by": VALIDATION_TESTS, "stamped": stamped}) + "\n")
    print(f"stamped {len(stamped)} rule(s)")


if __name__ == "__main__":
    main()
