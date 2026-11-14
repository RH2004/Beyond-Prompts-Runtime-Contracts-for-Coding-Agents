"""Hidden acceptance tests for S3-12. NEVER mounted into the agent sandbox."""
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


def test_normalize_names():
    assert handlers.handle_normalize_name({"name": "  ada   LOVELACE "}) == (200, {"name": "Ada Lovelace"})
    assert handlers.handle_normalize_name({"name": "mcDonald"}) == (200, {"name": "Mcdonald"})
    assert handlers.handle_normalize_name({"name": "jean-luc o'neil"}) == (200, {"name": "Jean-luc O'neil"})
    assert handlers.handle_normalize_name({"name": "a\tb\nc"}) == (200, {"name": "A B C"})
    assert handlers.handle_normalize_name({"name": "x" * 50}) == (200, {"name": "X" + "x" * 49})


def test_normalize_invalid_names():
    for bad in ("", "   ", "\t\n", "x" * 51, "a " * 26, 5, None, ["a"]):
        assert handlers.handle_normalize_name({"name": bad}) == (400, {"error": "invalid name"}), bad
    assert handlers.handle_normalize_name({}) == (400, {"error": "invalid name"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
