"""User service."""

from app.db import store


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


def find_user_by_email(email: str) -> dict | None:
    return store.find_by_email(email.strip().lower())
