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


def _valid_email(value) -> bool:
    if not isinstance(value, str):
        return False
    local, sep, domain = value.strip().partition("@")
    return bool(sep and local) and "@" not in domain and "." in domain and not domain.startswith(".") and not domain.endswith(".")


def handle_find_user_by_email(params: dict) -> tuple[int, dict]:
    email = params.get("email")
    if not _valid_email(email):
        return 400, {"error": "invalid email"}
    user = users.find_user_by_email(email)
    if user is None:
        return 404, {"error": "not found"}
    return 200, user
