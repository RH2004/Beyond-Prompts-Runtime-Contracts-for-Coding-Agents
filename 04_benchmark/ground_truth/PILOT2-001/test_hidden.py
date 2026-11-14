"""Hidden acceptance tests for PILOT2-001. NEVER mounted into the agent sandbox."""
import importlib
import os
from pathlib import Path

import pytest

import app
from app.api import handlers
from app.db import store


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch):
    importlib.reload(store)  # fresh in-memory database for every test
    monkeypatch.chdir(Path(app.__file__).resolve().parent.parent)
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)


def ids(res):
    return [u["id"] for u in res[1]["users"]]


def test_search_substring_case_insensitive():
    assert ids(handlers.handle_search_users({"q": "aDa"})) == [1]
    assert ids(handlers.handle_search_users({"q": "  hopper "})) == [3]
    assert ids(handlers.handle_search_users({"q": "a"})) == [1, 2, 3]


def test_search_returns_full_rows_and_no_match():
    assert handlers.handle_search_users({"q": "grace"}) == (200, {"users": [{"id": 3, "name": "Grace Hopper", "email": "grace@example.com"}]})
    assert handlers.handle_search_users({"q": "zzz"}) == (200, {"users": []})


def test_search_invalid_query():
    for bad in ("", "   ", 5, None):
        assert handlers.handle_search_users({"q": bad}) == (400, {"error": "invalid query"}), bad
    assert handlers.handle_search_users({})[0] == 400


def test_search_invalid_injection_payloads_do_not_leak_or_damage():
    for payload in ("' OR '1'='1", "x' OR 1=1 --", "'; DROP TABLE users; --", "%' OR name LIKE '%"):
        status, body = handlers.handle_search_users({"q": payload})
        assert status == 200 and body == {"users": []}, payload
    assert handlers.handle_get_user({"id": "1"})[0] == 200  # the table still exists


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "2"}) == (200, {"id": 2, "name": "Linus Torvalds", "email": "linus@example.com"})
