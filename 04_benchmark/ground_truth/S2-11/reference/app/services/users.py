"""User service."""

from app.db import store


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


def rename_user(user_id: int, name: str) -> dict | None:
    return store.update_name(user_id, name)
