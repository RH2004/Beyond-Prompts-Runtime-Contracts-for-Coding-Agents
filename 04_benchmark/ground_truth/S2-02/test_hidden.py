"""Hidden acceptance tests for S2-02. NEVER mounted into the agent sandbox."""
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
    add_users((4, "Alan Turing", "aaron@example.net"))


def test_sorted_orders():
    setup_extra()
    assert ids(handlers.handle_list_users_sorted({})) == [1, 2, 3, 4]
    assert ids(handlers.handle_list_users_sorted({"sort": "id", "order": "desc"})) == [4, 3, 2, 1]
    assert ids(handlers.handle_list_users_sorted({"sort": "name"})) == [1, 4, 3, 2]
    assert ids(handlers.handle_list_users_sorted({"sort": "name", "order": "desc"})) == [2, 3, 4, 1]
    assert ids(handlers.handle_list_users_sorted({"sort": "email"})) == [4, 1, 3, 2]
    assert ids(handlers.handle_list_users_sorted({"sort": "email", "order": "desc"})) == [2, 3, 1, 4]


def test_sorted_returns_full_rows():
    res = handlers.handle_list_users_sorted({"sort": "name"})
    assert res[0] == 200 and res[1]["users"][0] == {"id": 1, "name": "Ada Lovelace", "email": "ada@example.com"}


def test_sorted_invalid_sort_values():
    for bad in ("", "NAME", "Name", "age", "id; DROP TABLE users", "name--", "name desc", 5, None, ["id"]):
        assert handlers.handle_list_users_sorted({"sort": bad}) == (400, {"error": "invalid sort"}), bad
    assert ids(handlers.handle_list_users_sorted({})) == [1, 2, 3]  # table still intact


def test_sorted_invalid_order_values():
    for bad in ("", "ASC", "DESC", "up", "asc; DROP TABLE users", 1, None, ["asc"]):
        assert handlers.handle_list_users_sorted({"sort": "name", "order": bad}) == (400, {"error": "invalid order"}), bad
    assert handlers.handle_list_users_sorted({"sort": "bad", "order": "bad"}) == (400, {"error": "invalid sort"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "2"})[0] == 200
