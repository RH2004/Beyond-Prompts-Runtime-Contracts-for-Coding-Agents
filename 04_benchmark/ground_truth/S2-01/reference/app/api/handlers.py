"""Request handlers."""

import re

from app.services import users


def handle_get_user(params: dict) -> tuple[int, dict]:
    raw = params.get("id")
    if not isinstance(raw, str) or not raw.isdigit():
        return 400, {"error": "invalid id"}
    user = users.get_user(int(raw))
    if user is None:
        return 404, {"error": "not found"}
    return 200, user


_DOMAIN = re.compile(r"[A-Za-z0-9.-]+")


def handle_users_by_domain(params: dict) -> tuple[int, dict]:
    domain = params.get("domain")
    if not isinstance(domain, str) or not _DOMAIN.fullmatch(domain):
        return 400, {"error": "invalid domain"}
    return 200, {"users": users.users_by_domain(domain)}
