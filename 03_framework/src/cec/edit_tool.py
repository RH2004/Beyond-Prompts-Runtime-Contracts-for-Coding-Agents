"""Dedicated edit/write tool, identical in every condition (decision 0002-A2).

The tool separates *propose* from *apply*, so C4 can evaluate a change before any byte is written.
Its messages are behaviourally neutral: no guidance, warnings or validation beyond what an editor needs.
"""

import base64
import difflib
import posixpath
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

def _tool(name: str, description: str, props: dict, required: list) -> dict:
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": {"type": "object", "properties": props, "required": required}}}


_S = {"type": "string"}
# Flat tools (decision 0002-A2, revised 2026-11-02): one action per tool, the names coding models reach for.
EDIT_TOOLS = [
    _tool("view", "View a file in the repository, with line numbers (path relative to the repository root).",
          {"path": _S}, ["path"]),
    _tool("create", "Create a file, or overwrite it completely, in the repository.",
          {"path": _S, "file_text": {"type": "string", "description": "Full file content"}}, ["path", "file_text"]),
    _tool("str_replace", "Replace exactly one occurrence of old_str with new_str in a file of the repository.",
          {"path": _S, "old_str": {"type": "string", "description": "Exact text to replace; must occur exactly once"},
           "new_str": {"type": "string", "description": "Replacement text"}}, ["path", "old_str", "new_str"]),
]
EDIT_TOOL_NAMES = {t["function"]["name"] for t in EDIT_TOOLS}
# Names models habitually use for the same operations. Identical in every condition; every use is logged.
TOOL_ALIASES = {"read": "view", "read_file": "view", "view_file": "view", "write": "create", "write_file": "create",
                "create_file": "create", "replace": "str_replace"}


class EditError(Exception):
    """Invalid edit request; reported to the agent as a normal tool error."""


@dataclass
class ProposedEdit:
    path: str
    old_content: str | None  # None = file did not exist
    new_content: str

    @property
    def diff(self) -> str:
        old = (self.old_content or "").splitlines(keepends=True)
        new = self.new_content.splitlines(keepends=True)
        return "".join(difflib.unified_diff(old, new, f"a/{self.path}", f"b/{self.path}"))

    @property
    def added_lines(self) -> list[str]:
        return [l[1:] for l in self.diff.splitlines() if l.startswith("+") and not l.startswith("+++")]


REPO_ROOT = "/repo"


def normalize_path(path: str, root: str = REPO_ROOT) -> str:
    """Repository-relative POSIX path. Absolute paths under the repository root are accepted (models often use them);
    anything that escapes the root is rejected."""
    raw = path.replace("\\", "/")
    if raw == root or raw.startswith(root + "/"):
        raw = raw[len(root):].lstrip("/")
    p = posixpath.normpath(str(PurePosixPath(raw)))
    if p.startswith("/") or p == ".." or p.startswith("../") or p == ".":
        raise EditError(f"path must be inside the repository ({root}): {path}")
    return p


class LocalFileOps:
    """File access on the host filesystem (unit tests / dry runs)."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def read(self, path: str) -> str | None:
        f = self.root / path
        return f.read_text(encoding="utf-8") if f.is_file() else None

    def write(self, path: str, content: str) -> None:
        f = self.root / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8", newline="")


class DockerFileOps:
    """File access inside the sandbox container as the repository owner.

    Bash runs as a user with read-only access to the repository (see sandbox/Dockerfile), so this tool is the only
    write path in every condition. UNTESTED until Docker is available (smoke-test item 7a).
    """

    def __init__(self, container_id: str, repo_root: str, executable: str = "docker", user: str = "root"):
        self.container_id, self.repo_root, self.executable, self.user = container_id, repo_root, executable, user

    def _exec(self, script: str, stdin: str | None = None) -> subprocess.CompletedProcess:
        cmd = [self.executable, "exec", "-i", "-u", self.user, "-w", self.repo_root, self.container_id, "sh", "-c", script]
        return subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=60)

    def read(self, path: str) -> str | None:
        r = self._exec(f"test -f '{path}' && base64 '{path}'")
        return base64.b64decode(r.stdout).decode("utf-8") if r.returncode == 0 else None

    def write(self, path: str, content: str) -> None:
        payload = base64.b64encode(content.encode("utf-8")).decode()
        r = self._exec(f"mkdir -p \"$(dirname '{path}')\" && base64 -d > '{path}'", stdin=payload)
        if r.returncode != 0:
            raise OSError(f"write failed: {r.stderr.strip()}")


class EditTool:
    def __init__(self, fileops):
        self.fileops = fileops

    def view(self, path: str) -> str:
        path = normalize_path(path)
        content = self.fileops.read(path)
        if content is None:
            raise EditError(f"file not found: {path}")
        return "".join(f"{i:6d}\t{line}" for i, line in enumerate(content.splitlines(keepends=True), 1))

    def propose(self, args: dict) -> ProposedEdit:
        command, path = args.get("command"), normalize_path(args.get("path", ""))
        old = self.fileops.read(path)
        if command == "create":
            if "file_text" not in args:
                raise EditError("create requires file_text")
            if old == args["file_text"]:
                raise EditError(f"{path} already has exactly this content; the file was not changed")
            return ProposedEdit(path, old, args["file_text"])
        if command == "str_replace":
            if old is None:
                raise EditError(f"file not found: {path}")
            old_str, new_str = args.get("old_str"), args.get("new_str", "")
            if not old_str:
                raise EditError("str_replace requires old_str")
            if old_str == new_str:
                raise EditError("old_str and new_str are identical; the file was not changed")
            count = old.count(old_str)
            if count != 1:
                raise EditError(f"old_str must occur exactly once in {path}; found {count}")
            return ProposedEdit(path, old, old.replace(old_str, new_str, 1))
        raise EditError(f"unknown edit command: {command}")

    def apply(self, edit: ProposedEdit) -> str:
        self.fileops.write(edit.path, edit.new_content)
        return f"{'Created' if edit.old_content is None else 'Edited'} {edit.path}"
