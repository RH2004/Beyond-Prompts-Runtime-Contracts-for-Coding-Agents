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


_SORTS = ("id", "name", "email")


def handle_list_users_sorted(params: dict) -> tuple[int, dict]:
    sort = params.get("sort", "id")
    order = params.get("order", "asc")
    if not isinstance(sort, str) or sort not in _SORTS:
        return 400, {"error": "invalid sort"}
    if not isinstance(order, str) or order not in ("asc", "desc"):
        return 400, {"error": "invalid order"}
    return 200, {"users": users.list_users(sort, order == "desc")}
