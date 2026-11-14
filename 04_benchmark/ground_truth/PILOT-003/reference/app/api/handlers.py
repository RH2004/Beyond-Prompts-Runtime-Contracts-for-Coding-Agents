"""Request handlers. Handlers receive untrusted params and call app.services only."""

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


_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")


def handle_validate_email(params: dict) -> tuple[int, dict]:
    raw = params.get("email")
    if not isinstance(raw, str) or not _EMAIL.match(raw):
        return 400, {"valid": False, "error": "invalid email"}
    local, domain = raw.rsplit("@", 1)
    return 200, {"valid": True, "email": f"{local}@{domain.lower()}"}
