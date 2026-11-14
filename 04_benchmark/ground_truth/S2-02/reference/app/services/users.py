"""User service."""

from app.db import store


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


def list_users(sort: str, descending: bool) -> list[dict]:
    return sorted(store.list_all(), key=lambda u: u[sort], reverse=descending)
