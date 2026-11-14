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


def _digits(raw, default: int) -> int | None:
    if raw is None:
        return default
    if not isinstance(raw, str) or not raw.isdigit():
        return None
    return int(raw)


def handle_list_users(params: dict) -> tuple[int, dict]:
    page, size = _digits(params.get("page"), 1), _digits(params.get("page_size"), 10)
    if page is None or size is None or page < 1 or not 1 <= size <= 100:
        return 400, {"error": "invalid pagination"}
    found, total = users.list_users(page, size)
    return 200, {"users": found, "page": page, "page_size": size, "total": total}
