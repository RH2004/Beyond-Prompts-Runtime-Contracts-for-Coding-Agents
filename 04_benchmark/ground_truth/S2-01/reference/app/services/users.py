"""User service."""

from app.db import store


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


def users_by_domain(domain: str) -> list[dict]:
    return store.find_by_domain(domain)
