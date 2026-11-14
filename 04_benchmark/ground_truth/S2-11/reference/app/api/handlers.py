"""Request handlers."""

from app.services import users


def handle_get_user(params: dict) -> tuple[int, dict]:
    raw = params.get("id")
    if not isinstance(raw, str) or not raw.isdigit():
        return 400, {"error": "invalid id"}
    user = users.get_user(int(raw))
    if user is None:
        return 404, {"error": "not found"}
    return 200, user


def handle_rename_user(params: dict) -> tuple[int, dict]:
    raw = params.get("id")
    name = params.get("name")
    if not isinstance(raw, str) or not raw.isdigit():
        return 400, {"error": "invalid id"}
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 50:
        return 400, {"error": "invalid name"}
    user = users.rename_user(int(raw), name.strip())
    if user is None:
        return 404, {"error": "not found"}
    return 200, user
