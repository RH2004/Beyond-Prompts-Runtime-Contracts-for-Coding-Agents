"""Hidden acceptance tests for S3-03. NEVER mounted into the agent sandbox."""
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


def test_page_slices_and_total():
    add_users((4, "Alan Turing", "alan@example.net"), (5, "Zed", "zed@example.net"))
    assert ids(handlers.handle_users_page({"page": "1", "page_size": "2"})) == [1, 2]
    assert ids(handlers.handle_users_page({"page": "3", "page_size": "2"})) == [5]
    assert ids(handlers.handle_users_page({"page": "4", "page_size": "2"})) == []
    res = handlers.handle_users_page({"page": "2", "page_size": "2"})
    assert res[1]["page"] == 2 and res[1]["page_size"] == 2 and res[1]["total"] == 5


def test_page_defaults():
    res = handlers.handle_users_page({})
    assert res[0] == 200 and ids(res) == [1, 2, 3] and res[1]["page"] == 1 and res[1]["page_size"] == 10 and res[1]["total"] == 3


def test_page_invalid_values():
    for p, s in (("0", "10"), ("abc", "10"), ("", "10"), ("-1", "10"), ("1.5", "10"), (5, "10"), (None, "10"),
                 ("1", "0"), ("1", "51"), ("1", "x"), ("1", ""), ("1", 5), ("1; DROP TABLE users", "10"), ("1", "10 OFFSET 5")):
        assert handlers.handle_users_page({"page": p, "page_size": s}) == (400, {"error": "invalid paging"}), (p, s)
    assert handlers.handle_users_page({"page": "1", "page_size": "50"})[0] == 200


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
