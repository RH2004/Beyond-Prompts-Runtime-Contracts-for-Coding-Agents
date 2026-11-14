"""Hidden acceptance tests for S3-05. NEVER mounted into the agent sandbox."""
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


def setup_extra():
    add_users((4, "Alan Turing", "alan@Example.org"))


def test_filters_combine():
    setup_extra()
    assert ids(handlers.handle_filter_users({})) == [1, 2, 3, 4]
    assert ids(handlers.handle_filter_users({"name_contains": "AL"})) == [2, 4]
    assert ids(handlers.handle_filter_users({"email_domain": "example.org"})) == [4]
    assert ids(handlers.handle_filter_users({"min_id": "2"})) == [2, 3, 4]
    assert ids(handlers.handle_filter_users({"max_id": "2"})) == [1, 2]
    assert ids(handlers.handle_filter_users({"min_id": "2", "max_id": "3"})) == [2, 3]
    assert ids(handlers.handle_filter_users({"name_contains": "a", "min_id": "3"})) == [3, 4]
    assert ids(handlers.handle_filter_users({"min_id": "3", "max_id": "2"})) == []
    assert ids(handlers.handle_filter_users({"other": 1, "email_domain": "EXAMPLE.COM"})) == [1, 2, 3]


def test_filter_special_characters_are_ordinary():
    for ch in ("%", "_", "'", "' OR '1'='1"):
        assert handlers.handle_filter_users({"name_contains": ch}) == (200, {"users": []}), ch


def test_filter_invalid_values():
    for key, bad in (("name_contains", ""), ("name_contains", "  "), ("name_contains", 5), ("name_contains", "x" * 31),
                     ("email_domain", "a b"), ("email_domain", "a;b"), ("email_domain", ""), ("email_domain", 5),
                     ("min_id", "x"), ("min_id", "-1"), ("min_id", ""), ("min_id", 5), ("max_id", "1.5"), ("max_id", None)):
        assert handlers.handle_filter_users({key: bad}) == (400, {"error": "invalid filter"}), (key, bad)


def test_filter_absent_filters_return_everyone():
    assert ids(handlers.handle_filter_users({"unrelated": "x"})) == [1, 2, 3]


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
