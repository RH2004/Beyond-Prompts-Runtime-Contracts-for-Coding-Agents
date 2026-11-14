"""Hidden acceptance tests for S3-02. NEVER mounted into the agent sandbox."""
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


def test_ids_lookup():
    assert ids(handlers.handle_users_by_ids({"ids": ["3", "1"]})) == [1, 3]
    assert ids(handlers.handle_users_by_ids({"ids": ["1", "1", "01"]})) == [1]
    assert handlers.handle_users_by_ids({"ids": ["99"]}) == (200, {"users": []})
    assert ids(handlers.handle_users_by_ids({"ids": ["99", "2"]})) == [2]
    assert ids(handlers.handle_users_by_ids({"ids": [str(i) for i in range(1, 21)]})) == [1, 2, 3]


def test_ids_returns_full_rows():
    assert handlers.handle_users_by_ids({"ids": ["1"]})[1]["users"] == [{"id": 1, "name": "Ada Lovelace", "email": "ada@example.com"}]


def test_ids_invalid_values():
    for bad in ([], "1", None, ["1"] * 21, ["a"], [1], ["1", None], ["-1"], ["1;2"], [""], ["1 OR 1=1"], {"1": 1}):
        assert handlers.handle_users_by_ids({"ids": bad}) == (400, {"error": "invalid ids"}), bad


def test_ids_absent():
    assert handlers.handle_users_by_ids({}) == (400, {"error": "invalid ids"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
