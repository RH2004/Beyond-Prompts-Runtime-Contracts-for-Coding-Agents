"""User service."""

from app.db import store


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


def email_taken(email: str) -> bool:
    return store.find_by_email(email.strip().lower()) is not None
