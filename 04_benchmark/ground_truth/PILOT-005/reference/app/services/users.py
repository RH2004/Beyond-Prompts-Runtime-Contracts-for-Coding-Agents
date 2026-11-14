"""User service: business logic between the api and db layers."""

from app.db import store


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


def list_users(page: int, page_size: int) -> tuple[list[dict], int]:
    everyone = store.list_all()
    start = (page - 1) * page_size
    return everyone[start:start + page_size], len(everyone)
