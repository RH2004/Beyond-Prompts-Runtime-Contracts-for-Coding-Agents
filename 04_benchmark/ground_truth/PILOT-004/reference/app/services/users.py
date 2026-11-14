"""User service: business logic between the api and db layers."""

from app.db import store


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


def user_exists(user_id: int) -> bool:
    return store.get_by_id(user_id) is not None
