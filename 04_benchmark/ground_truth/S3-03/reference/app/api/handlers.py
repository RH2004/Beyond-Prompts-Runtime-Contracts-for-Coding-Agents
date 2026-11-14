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


def handle_users_page(params: dict) -> tuple[int, dict]:
    page, size = params.get("page", "1"), params.get("page_size", "10")
    if not (isinstance(page, str) and page.isdigit() and isinstance(size, str) and size.isdigit()):
        return 400, {"error": "invalid paging"}
    page, size = int(page), int(size)
    if page < 1 or not 1 <= size <= 50:
        return 400, {"error": "invalid paging"}
    everyone = users.all_users()
    start = (page - 1) * size
    return 200, {"users": everyone[start:start + size], "page": page, "page_size": size, "total": len(everyone)}
