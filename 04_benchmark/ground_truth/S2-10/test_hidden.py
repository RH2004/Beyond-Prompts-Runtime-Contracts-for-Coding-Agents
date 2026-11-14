"""Hidden acceptance tests for S2-10. NEVER mounted into the agent sandbox."""
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


def test_email_available_values():
    assert handlers.handle_email_available({"email": "new@example.com"}) == (200, {"available": True})
    assert handlers.handle_email_available({"email": "ada@example.com"}) == (200, {"available": False})
    assert handlers.handle_email_available({"email": " GRACE@EXAMPLE.COM "}) == (200, {"available": False})


def test_email_available_invalid():
    for bad in ("", "ada", "a@b", "@example.com", "a@@example.com", "a@b@example.com", "a@.com", "a@example.", "  ", "ada@example.com@", 5, None, ["a@b.c"]):
        assert handlers.handle_email_available({"email": bad}) == (400, {"error": "invalid email"}), bad


def test_email_available_absent():
    assert handlers.handle_email_available({}) == (400, {"error": "invalid email"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
