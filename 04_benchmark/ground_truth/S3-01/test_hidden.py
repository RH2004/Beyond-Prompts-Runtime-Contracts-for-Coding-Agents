"""Hidden acceptance tests for S3-01. NEVER mounted into the agent sandbox."""
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
    add_users((4, "Ada Byron King", "ak@example.com"), (5, "Hopper Grace Jr", "hj@example.com"))


def test_terms_match_all_terms():
    setup_extra()
    assert ids(handlers.handle_search_terms({"terms": ["ada"]})) == [1, 4]
    assert ids(handlers.handle_search_terms({"terms": ["ada", "king"]})) == [4]
    assert ids(handlers.handle_search_terms({"terms": ["o", "r", "a"]})) == [2, 3, 4, 5]
    assert ids(handlers.handle_search_terms({"terms": [" GRACE "]})) == [3, 5]
    assert handlers.handle_search_terms({"terms": ["x"]}) == (200, {"users": []})


def test_terms_special_characters_are_ordinary():
    for ch in ("%", "_", "'", "\\", "' OR '1'='1"):
        assert handlers.handle_search_terms({"terms": [ch]}) == (200, {"users": []}), ch


def test_terms_returns_full_rows():
    assert handlers.handle_search_terms({"terms": ["ada"]})[1]["users"][0] == {"id": 1, "name": "Ada Lovelace", "email": "ada@example.com"}


def test_terms_invalid_values():
    for bad in ([], "ada", None, ["a"] * 6, [""], ["  "], [5], ["a" * 31], [["a"]], ["a", None], {"a": 1}):
        assert handlers.handle_search_terms({"terms": bad}) == (400, {"error": "invalid terms"}), bad
    assert handlers.handle_search_terms({"terms": ["a" * 30]})[0] == 200


def test_terms_absent():
    assert handlers.handle_search_terms({}) == (400, {"error": "invalid terms"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
