"""Request handlers."""

import hmac

from app import config
from app.services import users


def handle_get_user(params: dict) -> tuple[int, dict]:
    raw = params.get("id")
    if not isinstance(raw, str) or not raw.isdigit():
        return 400, {"error": "invalid id"}
    user = users.get_user(int(raw))
    if user is None:
        return 404, {"error": "not found"}
    return 200, user


def handle_delete_user(params: dict) -> tuple[int, dict]:
    expected, given = config.get_setting("ADMIN_TOKEN"), params.get("token")
    if not expected or not isinstance(given, str) or not hmac.compare_digest(given.encode(), expected.encode()):
        return 403, {"error": "forbidden"}
    raw = params.get("id")
    if not isinstance(raw, str) or not raw.isdigit():
        return 400, {"error": "invalid id"}
    if not users.delete_user(int(raw)):
        return 404, {"error": "not found"}
    return 200, {"deleted": int(raw)}
