"""User service."""

from app.db import store


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


def all_users() -> list[dict]:
    return store.list_all()
