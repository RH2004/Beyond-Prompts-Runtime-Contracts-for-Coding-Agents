"""In-memory persistence layer. Only app.services may import this module."""

_USERS = {
    1: {"id": 1, "name": "Ada", "email": "ada@example.com"},
    2: {"id": 2, "name": "Linus", "email": "linus@example.com"},
}


def get_by_id(user_id: int) -> dict | None:
    user = _USERS.get(user_id)
    return dict(user) if user else None


def find_by_email(email: str) -> dict | None:
    for user in _USERS.values():
        if user["email"] == email:
            return dict(user)
    return None


def list_all() -> list[dict]:
    return [dict(u) for _, u in sorted(_USERS.items())]


def add(name: str, email: str) -> dict:
    new_id = max(_USERS, default=0) + 1
    _USERS[new_id] = {"id": new_id, "name": name, "email": email}
    return dict(_USERS[new_id])
