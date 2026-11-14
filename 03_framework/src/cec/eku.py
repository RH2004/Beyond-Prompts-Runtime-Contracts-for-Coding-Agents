"""Load and validate Engineering Knowledge Units; render them for each delivery mode."""

import fnmatch
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import jsonschema
import yaml

# Which stage each check kind evaluates, and on what target.
KIND_STAGE = {
    "command_deny": "pre_action",  # target: bash command string
    "path_deny": "pre_action",  # target: proposed edit path
    "content_deny": "pre_action",  # target: lines added by a proposed edit
    "import_deny": "post_edit",  # target: file content after an applied edit
    "output_deny": "post_execution",  # target: output of an executed command
    "repo_command": "pre_acceptance",  # target: repository state
}


@dataclass(frozen=True)
class EKU:
    data: dict

    @property
    def id(self) -> str:
        return self.data["id"]

    @property
    def severity(self) -> str:
        return self.data["severity"]

    @property
    def check(self) -> dict:
        return self.data["check"]

    @property
    def stage(self) -> str:
        return KIND_STAGE[self.check["kind"]]

    @property
    def spec_hash(self) -> str:
        return hashlib.sha256(json.dumps(self.check, sort_keys=True).encode()).hexdigest()[:16]

    def in_scope(self, path: str) -> bool:
        globs = self.data.get("scope", {}).get("paths") or []
        return not globs or any(fnmatch.fnmatch(path, g) for g in globs)

    def render_prose(self) -> str:
        """C1/C1r rendering: title, rationale, one example if present."""
        d = self.data
        text = f"- {d['title']}. {d['rationale']}"
        if scope := d.get("scope", {}).get("paths"):
            text += f" (Applies to: {', '.join(scope)}.)"
        return text

    def render_record(self) -> dict:
        """C2+ rendering: structured record returned by lookup_rules / scope surfacing."""
        d = self.data
        return {
            "id": d["id"],
            "title": d["title"],
            "category": d["category"],
            "severity": d["severity"],
            "scope": d.get("scope", {}),
            "rationale": d["rationale"],
        }


def load_schema(schema_path: Path) -> dict:
    return json.loads(Path(schema_path).read_text(encoding="utf-8"))


def load_library(rules_dir: Path, schema_path: Path) -> dict[str, EKU]:
    """Load every *.yaml under rules_dir, validate against the schema, and check stage/kind consistency."""
    schema = load_schema(schema_path)
    library = {}
    for path in sorted(Path(rules_dir).rglob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        jsonschema.validate(data, schema)
        eku = EKU(data)
        if eku.stage not in data["stage"]:
            raise ValueError(f"{eku.id}: check kind {eku.check['kind']} runs at {eku.stage}, not in stage {data['stage']}")
        if eku.id in library:
            raise ValueError(f"duplicate EKU id {eku.id}")
        if path.stem != eku.id:
            raise ValueError(f"{path.name}: filename must equal EKU id {eku.id}")
        library[eku.id] = eku
    return library


def check_fresh(eku: EKU) -> bool:
    """Stale evidence -> unknown (decision 0014). An EKU without evidence_hash has never been validated."""
    recorded = eku.data.get("evidence_hash")
    return recorded is not None and recorded == eku.spec_hash
