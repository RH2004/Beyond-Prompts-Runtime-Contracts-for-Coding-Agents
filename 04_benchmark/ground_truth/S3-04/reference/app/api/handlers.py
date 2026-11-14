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


def handle_group_counts(params: dict) -> tuple[int, dict]:
    by = params.get("by")
    if by not in ("domain", "initial") or not isinstance(by, str):
        return 400, {"error": "invalid grouping"}
    groups: dict[str, int] = {}
    for user in users.all_users():
        key = user["email"].rsplit("@", 1)[1].lower() if by == "domain" else user["name"][:1].upper()
        groups[key] = groups.get(key, 0) + 1
    return 200, {"groups": groups}
