"""Request handlers."""

from datetime import datetime

from app.services import users


def handle_get_user(params: dict) -> tuple[int, dict]:
    raw = params.get("id")
    if not isinstance(raw, str) or not raw.isdigit():
        return 400, {"error": "invalid id"}
    user = users.get_user(int(raw))
    if user is None:
        return 404, {"error": "not found"}
    return 200, user


_DATE_FORMATS = ("%Y-%m-%d", "%d %b %Y", "%B %d, %Y", "%d/%m/%Y")


def handle_normalize_date(params: dict) -> tuple[int, dict]:
    value = params.get("date")
    if not isinstance(value, str):
        return 400, {"error": "invalid date"}
    text = value.strip()
    for fmt in _DATE_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return 200, {"date": parsed.date().isoformat()}
    return 400, {"error": "invalid date"}
