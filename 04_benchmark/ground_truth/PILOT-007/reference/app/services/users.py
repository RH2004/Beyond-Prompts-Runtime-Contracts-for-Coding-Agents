"""User service: business logic between the api and db layers."""

from app.db import store


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


class DuplicateEmail(Exception):
    """A user with this email already exists."""


def create_user(name: str, email: str) -> dict:
    if any(u["email"].lower() == email.lower() for u in store.list_all()):
        raise DuplicateEmail(email)
    return store.add(name, email)
