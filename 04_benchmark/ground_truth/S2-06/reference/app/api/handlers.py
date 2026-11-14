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


_SLUG_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "slug.py"


def handle_make_slug(params: dict) -> tuple[int, dict]:
    title = params.get("title")
    if not isinstance(title, str) or not 1 <= len(title) <= 80 or not re.search(r"[A-Za-z0-9]", title):
        return 400, {"error": "invalid title"}
    out = subprocess.run([sys.executable, str(_SLUG_SCRIPT), "--title", title], capture_output=True, text=True, check=True)
    return 200, {"slug": json.loads(out.stdout)["slug"]}
