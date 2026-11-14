"""User service: business logic between the api and db layers."""

from app.db import store


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


def search_users(query: str) -> list[dict]:
    needle = query.strip().lower()
    return [u for u in store.list_all() if needle in u["name"].lower() or needle in u["email"].lower()]
