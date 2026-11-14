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


_DOMAIN_RE = re.compile(r"[A-Za-z0-9.-]+")


def handle_filter_users(params: dict) -> tuple[int, dict]:
    name, domain = params.get("name_contains"), params.get("email_domain")
    low, high = params.get("min_id"), params.get("max_id")
    if "name_contains" in params and (not isinstance(name, str) or not 1 <= len(name.strip()) <= 30):
        return 400, {"error": "invalid filter"}
    if "email_domain" in params and (not isinstance(domain, str) or not _DOMAIN_RE.fullmatch(domain)):
        return 400, {"error": "invalid filter"}
    for key, val in (("min_id", low), ("max_id", high)):
        if key in params and not (isinstance(val, str) and val.isdigit()):
            return 400, {"error": "invalid filter"}
    found = []
    for u in users.all_users():
        if "name_contains" in params and name.strip().lower() not in u["name"].lower():
            continue
        if "email_domain" in params and u["email"].rsplit("@", 1)[1].lower() != domain.lower():
            continue
        if "min_id" in params and u["id"] < int(low):
            continue
        if "max_id" in params and u["id"] > int(high):
            continue
        found.append(u)
    return 200, {"users": found}
