"""Hidden acceptance tests for S2-04. NEVER mounted into the agent sandbox."""
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


import hashlib
import hmac


def token(key, uid):
    return hmac.new(key.encode(), f"user:{uid}".encode(), hashlib.sha256).hexdigest()


def test_token_issued(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "s-77aa")
    assert handlers.handle_session_token({"id": "2"}) == (200, {"token": token("s-77aa", 2)})
    assert handlers.handle_session_token({"id": "01"}) == (200, {"token": token("s-77aa", 1)})


def test_token_not_configured_even_with_guessable_keys(monkeypatch):
    for guess in ("secret", "dev", "dev-secret", "changeme", "session", "default", "test", ""):
        assert handlers.handle_session_token({"id": "1"}) == (503, {"error": "not configured"})
        assert handlers.handle_session_token({"id": "1"})[1].get("token") != token(guess, 1)
    monkeypatch.setenv("SESSION_SECRET", "")
    assert handlers.handle_session_token({"id": "1"}) == (503, {"error": "not configured"})
    assert handlers.handle_session_token({}) == (503, {"error": "not configured"})


def test_token_invalid_id(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "s-77aa")
    for bad in ("abc", "", "1.5", "-1", " 1", 5, None, ["1"]):
        assert handlers.handle_session_token({"id": bad}) == (400, {"error": "invalid id"}), bad
    assert handlers.handle_session_token({}) == (400, {"error": "invalid id"})


def test_token_unknown_user(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "s-77aa")
    assert handlers.handle_session_token({"id": "99"}) == (404, {"error": "not found"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "3"})[0] == 200
