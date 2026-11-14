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


def handle_search_users(params: dict) -> tuple[int, dict]:
    query = params.get("q")
    if not isinstance(query, str) or not query.strip():
        return 400, {"error": "invalid query"}
    return 200, {"users": users.search_users(query)}
