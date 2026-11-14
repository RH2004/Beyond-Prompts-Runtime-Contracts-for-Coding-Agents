"""Request handlers. Handlers receive untrusted params and call app.services only."""

import re

from app.services import users

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def handle_get_user(params: dict) -> tuple[int, dict]:
    raw = params.get("id")
    if not isinstance(raw, str) or not raw.isdigit():
        return 400, {"error": "invalid id"}
    user = users.get_user(int(raw))
    if user is None:
        return 404, {"error": "not found"}
    return 200, user


def handle_get_user_by_email(params: dict) -> tuple[int, dict]:
    email = params.get("email")
    if not isinstance(email, str) or not _EMAIL.match(email):
        return 400, {"error": "invalid email"}
    user = users.find_user_by_email(email)
    if user is None:
        return 404, {"error": "not found"}
    return 200, user
