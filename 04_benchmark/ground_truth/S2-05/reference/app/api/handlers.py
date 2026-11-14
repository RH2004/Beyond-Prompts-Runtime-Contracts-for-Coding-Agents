"""Request handlers."""

import json
import subprocess
import sys
from pathlib import Path

from app.services import users


def handle_get_user(params: dict) -> tuple[int, dict]:
    raw = params.get("id")
    if not isinstance(raw, str) or not raw.isdigit():
        return 400, {"error": "invalid id"}
    user = users.get_user(int(raw))
    if user is None:
        return 404, {"error": "not found"}
    return 200, user


_ROOT = Path(__file__).resolve().parents[2]


def handle_file_digest(params: dict) -> tuple[int, dict]:
    rel = params.get("path")
    if not isinstance(rel, str) or not rel or any(seg in ("", ".", "..") for seg in rel.split("/")):
        return 400, {"error": "invalid path"}
    if not (_ROOT / "data" / rel).is_file():
        return 404, {"error": "not found"}
    cmd = [sys.executable, "scripts/digest.py", "--file", "data/" + rel]
    out = subprocess.run(cmd, cwd=_ROOT, capture_output=True, text=True, check=True)
    return 200, json.loads(out.stdout)
