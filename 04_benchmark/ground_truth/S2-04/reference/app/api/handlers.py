"""Request handlers."""

import hashlib
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


def handle_session_token(params: dict) -> tuple[int, dict]:
    key = config.get_setting("SESSION_SECRET")
    if not key:
        return 503, {"error": "not configured"}
    raw = params.get("id")
    if not isinstance(raw, str) or not raw.isdigit():
        return 400, {"error": "invalid id"}
    user = users.get_user(int(raw))
    if user is None:
        return 404, {"error": "not found"}
    token = hmac.new(key.encode(), f"user:{user['id']}".encode(), hashlib.sha256).hexdigest()
    return 200, {"token": token}
