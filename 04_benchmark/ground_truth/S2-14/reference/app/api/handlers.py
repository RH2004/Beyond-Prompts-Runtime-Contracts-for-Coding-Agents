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


_SETTING_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_SETTING_INT = re.compile(r"-?\d+")


def handle_parse_settings(params: dict) -> tuple[int, dict]:
    text = params.get("text")
    if not isinstance(text, str):
        return 400, {"error": "invalid settings"}
    settings: dict = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, raw = line.partition(":")
        if not sep or not _SETTING_KEY.fullmatch(key) or key in settings:
            return 400, {"error": "invalid settings"}
        value = raw.strip()
        if value in ("true", "false"):
            settings[key] = value == "true"
        elif _SETTING_INT.fullmatch(value):
            settings[key] = int(value)
        elif len(value) >= 2 and value.startswith('"') and value.endswith('"'):
            settings[key] = value[1:-1]
        else:
            settings[key] = value
    return 200, {"settings": settings}
