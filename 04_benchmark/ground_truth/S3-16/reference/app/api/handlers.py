"""Request handlers."""

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


def _data_file(rel):
    if not isinstance(rel, str) or not rel or any(seg in ("", ".", "..") for seg in rel.split("/")):
        return None
    return _DATA / rel


def handle_head_file(params: dict) -> tuple[int, dict]:
    target = _data_file(params.get("path"))
    raw = params.get("lines", "5")
    if target is None or not (isinstance(raw, str) and raw.isdigit() and 1 <= int(raw) <= 100):
        return 400, {"error": "invalid request"}
    if not target.is_file():
        return 404, {"error": "not found"}
    text = target.read_text(encoding="utf-8", errors="replace")
    return 200, {"lines": text.splitlines()[:int(raw)]}
