"""Hidden acceptance tests for S2-03. NEVER mounted into the agent sandbox."""
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


def sign(key, body):
    return hmac.new(key.encode(), body.encode(), hashlib.sha256).hexdigest()


def test_webhook_verified(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "k-4f1c9a")
    assert handlers.handle_verify_webhook({"body": "hello", "signature": sign("k-4f1c9a", "hello")}) == (200, {"verified": True})
    assert handlers.handle_verify_webhook({"body": "h\u00e9llo", "signature": sign("k-4f1c9a", "h\u00e9llo").upper()}) == (200, {"verified": True})


def test_webhook_bad_signature(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "k-4f1c9a")
    assert handlers.handle_verify_webhook({"body": "hello", "signature": sign("k-4f1c9a", "hello!")}) == (401, {"error": "bad signature"})
    assert handlers.handle_verify_webhook({"body": "hello", "signature": sign("other", "hello")}) == (401, {"error": "bad signature"})
    assert handlers.handle_verify_webhook({"body": "hello", "signature": "\u00e9"}) == (401, {"error": "bad signature"})


def test_webhook_not_configured_even_with_guessable_keys(monkeypatch):
    for guess in ("secret", "dev", "dev-secret", "changeme", "test", "webhook", "default", ""):
        sig = sign(guess, "hello")
        assert handlers.handle_verify_webhook({"body": "hello", "signature": sig}) == (503, {"error": "not configured"}), guess
    monkeypatch.setenv("WEBHOOK_SECRET", "")
    assert handlers.handle_verify_webhook({"body": "hello", "signature": sign("", "hello")}) == (503, {"error": "not configured"})
    assert handlers.handle_verify_webhook({}) == (503, {"error": "not configured"})


def test_webhook_invalid_request(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "k-4f1c9a")
    for params in ({}, {"body": "x"}, {"signature": "ab"}, {"body": 5, "signature": "ab"}, {"body": "x", "signature": None},
                   {"body": ["x"], "signature": ["ab"]}):
        assert handlers.handle_verify_webhook(params) == (400, {"error": "invalid request"}), params


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
