"""Request handlers."""

import re
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


_DATA = Path(__file__).resolve().parents[2] / "data"


def _data_dir(params: dict):
    rel = params.get("dir", "")
    if not isinstance(rel, str) or (rel and any(seg in ("", ".", "..") for seg in rel.split("/"))):
        return None, (400, {"error": "invalid path"})
    target = _DATA / rel
    if not target.is_dir():
        return None, (404, {"error": "not found"})
    return target, None

_EXT = re.compile(r"[A-Za-z0-9]{1,8}")


def handle_find_by_extension(params: dict) -> tuple[int, dict]:
    ext = params.get("ext")
    if not isinstance(ext, str) or not _EXT.fullmatch(ext):
        return 400, {"error": "invalid extension"}
    target, err = _data_dir(params)
    if err:
        return err
    suffix = "." + ext.lower()
    found = sorted(p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file() and p.name.lower().endswith(suffix))
    return 200, {"files": found}
