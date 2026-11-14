"""Request handlers. Handlers receive untrusted params and call app.services only."""

from app.services import users


def handle_get_user(params: dict) -> tuple[int, dict]:
    raw = params.get("id")
    if not isinstance(raw, str) or not raw.isdigit():
        return 400, {"error": "invalid id"}
    user = users.get_user(int(raw))
    if user is None:
        return 404, {"error": "not found"}
    return 200, user


def handle_filter_users(params: dict) -> tuple[int, dict]:
    expression = params.get("where")
    if not isinstance(expression, str) or not expression.strip():
        return 400, {"error": "invalid filter"}
    try:
        found = users.filter_users(expression)
    except users.InvalidFilter:
        return 400, {"error": "invalid filter"}
    return 200, {"users": found}
