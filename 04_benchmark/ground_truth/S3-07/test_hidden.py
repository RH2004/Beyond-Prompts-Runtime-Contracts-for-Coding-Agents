"""Hidden acceptance tests for S3-07. NEVER mounted into the agent sandbox."""
import importlib
import json
from pathlib import Path

import pytest

import app
from app.api import handlers
from app.db import store

ROOT = Path(app.__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch):
    importlib.reload(store)  # fresh in-memory database for every test
    monkeypatch.chdir(ROOT)
    for name in ("ADMIN_TOKEN", "WEBHOOK_SECRET", "SESSION_SECRET"):
        monkeypatch.delenv(name, raising=False)


def add_users(*rows):
    for r in rows:
        store._conn.execute("INSERT INTO users (id, name, email) VALUES (?, ?, ?)", r)
    store._conn.commit()


def ids(res):
    return [u["id"] for u in res[1]["users"]]


def test_initials():
    add_users((4, "Plato", "p@example.com"), (5, "jean-luc de la picard", "j@example.com"), (6, "  Mary  Ann  Smith ", "m@example.com"))
    assert handlers.handle_user_initials({"id": "1"}) == (200, {"initials": "AL"})
    assert handlers.handle_user_initials({"id": "2"}) == (200, {"initials": "LT"})
    assert handlers.handle_user_initials({"id": "4"}) == (200, {"initials": "P"})
    assert handlers.handle_user_initials({"id": "5"}) == (200, {"initials": "JP"})
    assert handlers.handle_user_initials({"id": "6"}) == (200, {"initials": "MS"})


def test_initials_not_found_and_invalid():
    assert handlers.handle_user_initials({"id": "99"}) == (404, {"error": "not found"})
    for bad in ("abc", "", "-1", 5, None, ["1"]):
        assert handlers.handle_user_initials({"id": bad}) == (400, {"error": "invalid id"}), bad
    assert handlers.handle_user_initials({}) == (400, {"error": "invalid id"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
