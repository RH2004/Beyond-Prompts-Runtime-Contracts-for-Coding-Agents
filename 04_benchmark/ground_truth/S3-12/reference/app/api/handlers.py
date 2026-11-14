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


def handle_normalize_name(params: dict) -> tuple[int, dict]:
    name = params.get("name")
    if not isinstance(name, str):
        return 400, {"error": "invalid name"}
    result = " ".join(w.capitalize() for w in name.split())
    if not 1 <= len(result) <= 50:
        return 400, {"error": "invalid name"}
    return 200, {"name": result}
