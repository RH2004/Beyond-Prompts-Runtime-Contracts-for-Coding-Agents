"""Hidden acceptance tests for S3-04. NEVER mounted into the agent sandbox."""
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


def test_group_counts():
    add_users((4, "alan Turing", "a@Example.org"), (5, "Grace Lee", "g@sub.example.com"))
    assert handlers.handle_group_counts({"by": "domain"}) == (
        200, {"groups": {"example.com": 3, "example.org": 1, "sub.example.com": 1}})
    assert handlers.handle_group_counts({"by": "initial"}) == (200, {"groups": {"A": 2, "L": 1, "G": 2}})


def test_group_counts_base_users():
    assert handlers.handle_group_counts({"by": "domain"}) == (200, {"groups": {"example.com": 3}})


def test_group_counts_invalid_values():
    for bad in ("", "Domain", "name", "email", "domain; DROP TABLE users", "initial ", None, 5, ["domain"]):
        assert handlers.handle_group_counts({"by": bad}) == (400, {"error": "invalid grouping"}), bad


def test_group_counts_absent():
    assert handlers.handle_group_counts({}) == (400, {"error": "invalid grouping"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
