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


def handle_verify_webhook(params: dict) -> tuple[int, dict]:
    key = config.get_setting("WEBHOOK_SECRET")
    if not key:
        return 503, {"error": "not configured"}
    body, signature = params.get("body"), params.get("signature")
    if not isinstance(body, str) or not isinstance(signature, str):
        return 400, {"error": "invalid request"}
    expected = hmac.new(key.encode(), body.encode(), hashlib.sha256).hexdigest()
    if hmac.compare_digest(expected.encode(), signature.lower().encode()):
        return 200, {"verified": True}
    return 401, {"error": "bad signature"}
