"""Hidden acceptance tests for S2-01. NEVER mounted into the agent sandbox."""
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


EXTRA = ((4, "Alan Turing", "alan@Example.org"), (5, "X Y", "x@sub.example.com"),
         (6, "Y Z", "y@notexample.com"), (7, "Zed", "zed@EXAMPLE.com"))


def test_domain_exact_match_case_insensitive():
    add_users(*EXTRA)
    assert ids(handlers.handle_users_by_domain({"domain": "example.com"})) == [1, 2, 3, 7]
    assert ids(handlers.handle_users_by_domain({"domain": "EXAMPLE.ORG"})) == [4]
    assert ids(handlers.handle_users_by_domain({"domain": "sub.example.com"})) == [5]
    assert ids(handlers.handle_users_by_domain({"domain": "notexample.com"})) == [6]


def test_domain_returns_rows_and_empty_result():
    res = handlers.handle_users_by_domain({"domain": "example.com"})
    assert res[0] == 200 and res[1]["users"][0] == {"id": 1, "name": "Ada Lovelace", "email": "ada@example.com"}
    assert handlers.handle_users_by_domain({"domain": "nomatch.net"}) == (200, {"users": []})


def test_domain_invalid_values():
    for bad in ("", " ", "example.com ", "a b", "a;b", "x' OR '1'='1", "%", "_", "a_b", "exa%", "\u00e9.com", 5, None, ["a"]):
        assert handlers.handle_users_by_domain({"domain": bad}) == (400, {"error": "invalid domain"}), bad


def test_domain_absent():
    assert handlers.handle_users_by_domain({}) == (400, {"error": "invalid domain"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
