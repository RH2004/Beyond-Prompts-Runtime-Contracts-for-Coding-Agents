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


def handle_count_users(params: dict) -> tuple[int, dict]:
    domain = params.get("domain")
    if "domain" in params and (not isinstance(domain, str) or not domain):
        return 400, {"error": "invalid domain"}
    return 200, {"count": users.count_users(domain)}
