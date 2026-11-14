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


def handle_create_user(params: dict) -> tuple[int, dict]:
    name, email = params.get("name"), params.get("email")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 50:
        return 400, {"error": "invalid user"}
    if not isinstance(email, str) or not _EMAIL.match(email):
        return 400, {"error": "invalid user"}
    try:
        return 201, users.create_user(name.strip(), email)
    except users.DuplicateEmail:
        return 409, {"error": "email already exists"}
