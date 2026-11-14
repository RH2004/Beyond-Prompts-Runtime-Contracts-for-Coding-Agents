"""User service."""

from app.db import store


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


def domain_counts() -> dict:
    counts: dict[str, int] = {}
    for user in store.list_all():
        domain = user["email"].rsplit("@", 1)[1].lower()
        counts[domain] = counts.get(domain, 0) + 1
    return counts
