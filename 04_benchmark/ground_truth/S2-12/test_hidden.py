"""Hidden acceptance tests for S2-12. NEVER mounted into the agent sandbox."""
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


def test_domain_counts_base_users():
    assert handlers.handle_domain_counts({}) == (200, {"domains": {"example.com": 3}})


def test_domain_counts_lowercases_and_groups():
    add_users((4, "Alan Turing", "alan@Example.org"), (5, "X Y", "x@sub.example.com"), (6, "Y Z", "y@EXAMPLE.COM"))
    assert handlers.handle_domain_counts({}) == (
        200, {"domains": {"example.com": 4, "example.org": 1, "sub.example.com": 1}})


def test_domain_counts_ignores_invalid_params():
    assert handlers.handle_domain_counts({"x": 5, "domain": None}) == (200, {"domains": {"example.com": 3}})


def test_domain_counts_absent_params_fields():
    assert handlers.handle_domain_counts({})[0] == 200


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
