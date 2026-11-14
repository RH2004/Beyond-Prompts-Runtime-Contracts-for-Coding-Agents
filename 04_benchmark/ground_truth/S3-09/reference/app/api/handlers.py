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


def handle_name_stats(params: dict) -> tuple[int, dict]:
    lengths = [len(u["name"]) for u in users.all_users()]
    return 200, {"count": len(lengths), "min": min(lengths), "max": max(lengths), "average": round(sum(lengths) / len(lengths), 2)}
