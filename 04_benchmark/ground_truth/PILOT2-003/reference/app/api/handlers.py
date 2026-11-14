"""Request handlers."""

import json
import re
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


_NAME = re.compile(r"[A-Za-z0-9_-]{1,32}")
_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "report.py"


def handle_user_report(params: dict) -> tuple[int, dict]:
    name = params.get("name")
    if not isinstance(name, str) or not _NAME.fullmatch(name):
        return 400, {"error": "invalid name"}
    out = subprocess.run([sys.executable, str(_SCRIPT), "--name", name], capture_output=True, text=True, check=True)
    return 200, json.loads(out.stdout)
