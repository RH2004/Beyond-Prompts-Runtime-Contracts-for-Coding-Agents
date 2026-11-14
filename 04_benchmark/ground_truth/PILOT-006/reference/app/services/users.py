"""User service: business logic between the api and db layers."""

from app.db import store


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


def count_users(domain: str | None = None) -> int:
    everyone = store.list_all()
    if domain is None:
        return len(everyone)
    wanted = domain.lower()
    return sum(1 for u in everyone if u["email"].rsplit("@", 1)[-1].lower() == wanted)
