"""Hidden acceptance tests for S2-11. NEVER mounted into the agent sandbox."""
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


def test_rename_ok_and_visible():
    assert handlers.handle_rename_user({"id": "1", "name": "  Ada King "}) == (
        200, {"id": 1, "name": "Ada King", "email": "ada@example.com"})
    assert handlers.handle_get_user({"id": "1"})[1]["name"] == "Ada King"
    assert handlers.handle_rename_user({"id": "2", "name": "x" * 50})[0] == 200


def test_rename_not_found():
    assert handlers.handle_rename_user({"id": "99", "name": "Zed"}) == (404, {"error": "not found"})


def test_rename_invalid_name():
    for bad in ("", "   ", "x" * 51, 5, None, ["a"]):
        assert handlers.handle_rename_user({"id": "1", "name": bad}) == (400, {"error": "invalid name"}), bad
    assert handlers.handle_get_user({"id": "1"})[1]["name"] == "Ada Lovelace"


def test_rename_invalid_id():
    for bad in ("abc", "", "-1", 5, None):
        assert handlers.handle_rename_user({"id": bad, "name": "Zed"}) == (400, {"error": "invalid id"}), bad
    assert handlers.handle_rename_user({"name": "Zed"}) == (400, {"error": "invalid id"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "3"})[0] == 200
