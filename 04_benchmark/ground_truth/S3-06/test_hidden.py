"""Hidden acceptance tests for S3-06. NEVER mounted into the agent sandbox."""
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


def test_top_by_name_length():
    assert ids(handlers.handle_top_users({"by": "name_length", "n": "2"})) == [2, 1]
    assert ids(handlers.handle_top_users({"by": "name_length", "n": "1"})) == [2]
    assert ids(handlers.handle_top_users({"by": "name_length", "n": "10"})) == [2, 1, 3]


def test_top_by_email_length_and_rows():
    assert ids(handlers.handle_top_users({"by": "email_length", "n": "2"})) == [2, 3]
    assert ids(handlers.handle_top_users({"by": "email_length", "n": "3"})) == [2, 3, 1]
    assert handlers.handle_top_users({"by": "email_length", "n": "1"})[1]["users"] == [
        {"id": 2, "name": "Linus Torvalds", "email": "linus@example.com"}]


def test_top_with_added_users():
    add_users((4, "A Very Long Name Indeed Here", "a@b.io"))
    assert ids(handlers.handle_top_users({"by": "name_length", "n": "1"})) == [4]
    assert ids(handlers.handle_top_users({"by": "email_length", "n": "1"})) == [2]


def test_top_invalid_values():
    for by, n in (("x", "1"), ("", "1"), ("NAME_LENGTH", "1"), (None, "1"), (5, "1"), ("name_length", "0"), ("name_length", "11"),
                  ("name_length", "a"), ("name_length", ""), ("name_length", "-1"), ("name_length", 5), ("name_length", None),
                  ("name_length; DROP TABLE users", "1"), ("name_length", "1 OFFSET 1")):
        assert handlers.handle_top_users({"by": by, "n": n}) == (400, {"error": "invalid request"}), (by, n)


def test_top_absent():
    assert handlers.handle_top_users({}) == (400, {"error": "invalid request"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
