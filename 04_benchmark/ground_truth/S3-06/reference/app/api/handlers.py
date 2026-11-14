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


def handle_top_users(params: dict) -> tuple[int, dict]:
    by, n = params.get("by"), params.get("n")
    if not isinstance(by, str) or by not in ("name_length", "email_length"):
        return 400, {"error": "invalid request"}
    if not isinstance(n, str) or not n.isdigit() or not 1 <= int(n) <= 10:
        return 400, {"error": "invalid request"}
    field = "name" if by == "name_length" else "email"
    ranked = sorted(users.all_users(), key=lambda u: (-len(u[field]), u["id"]))
    return 200, {"users": ranked[:int(n)]}
