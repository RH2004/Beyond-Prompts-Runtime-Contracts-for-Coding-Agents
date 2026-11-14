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


def handle_users_by_ids(params: dict) -> tuple[int, dict]:
    raw = params.get("ids")
    if not isinstance(raw, list) or not 1 <= len(raw) <= 20 or not all(isinstance(i, str) and i.isdigit() for i in raw):
        return 400, {"error": "invalid ids"}
    wanted = {int(i) for i in raw}
    return 200, {"users": [u for u in users.all_users() if u["id"] in wanted]}
