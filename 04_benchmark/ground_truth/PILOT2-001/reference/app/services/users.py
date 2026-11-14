"""User service."""

from app.db import store


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


def search_users(query: str) -> list[dict]:
    return store.search_by_name(query.strip())
