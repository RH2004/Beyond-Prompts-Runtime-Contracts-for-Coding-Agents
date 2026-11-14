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


def handle_search_terms(params: dict) -> tuple[int, dict]:
    terms = params.get("terms")
    if not isinstance(terms, list) or not 1 <= len(terms) <= 5:
        return 400, {"error": "invalid terms"}
    cleaned = []
    for t in terms:
        if not isinstance(t, str) or not 1 <= len(t.strip()) <= 30:
            return 400, {"error": "invalid terms"}
        cleaned.append(t.strip().lower())
    return 200, {"users": [u for u in users.all_users() if all(t in u["name"].lower() for t in cleaned)]}
