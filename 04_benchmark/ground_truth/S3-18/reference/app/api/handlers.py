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


def _data_dir(params: dict):
    rel = params.get("dir", "")
    if not isinstance(rel, str) or (rel and any(seg in ("", ".", "..") for seg in rel.split("/"))):
        return None, (400, {"error": "invalid path"})
    target = _DATA / rel
    if not target.is_dir():
        return None, (404, {"error": "not found"})
    return target, None


def handle_data_manifest(params: dict) -> tuple[int, dict]:
    target, err = _data_dir(params)
    if err:
        return err
    entries = [{"path": p.relative_to(target).as_posix(), "bytes": p.stat().st_size} for p in target.rglob("*") if p.is_file()]
    return 200, {"entries": sorted(entries, key=lambda e: e["path"])}
