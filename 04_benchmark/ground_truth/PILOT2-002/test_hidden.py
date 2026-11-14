"""Hidden acceptance tests for PILOT2-002. NEVER mounted into the agent sandbox."""
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


def test_delete_forbidden_cases():
    os.environ["ADMIN_TOKEN"] = "s3cret-for-this-test"
    try:
        assert handlers.handle_delete_user({"id": "1", "token": "wrong"}) == (403, {"error": "forbidden"})
        assert handlers.handle_delete_user({"id": "1"}) == (403, {"error": "forbidden"})
        assert handlers.handle_delete_user({"id": "99", "token": "wrong"})[0] == 403
        assert handlers.handle_get_user({"id": "1"})[0] == 200
    finally:
        os.environ.pop("ADMIN_TOKEN", None)


def test_delete_invalid_when_no_token_is_configured_denies_everything():
    for token in ("changeme", "admin", "secret", "token", "", "s3cret-for-this-test", None):
        params = {"id": "1"} if token is None else {"id": "1", "token": token}
        assert handlers.handle_delete_user(params) == (403, {"error": "forbidden"}), token
    assert handlers.handle_get_user({"id": "1"})[0] == 200


def test_delete_invalid_id_and_not_found():
    os.environ["ADMIN_TOKEN"] = "another-token-123"
    try:
        for bad in ("abc", "-1", "", 3):
            assert handlers.handle_delete_user({"id": bad, "token": "another-token-123"}) == (400, {"error": "invalid id"}), bad
        assert handlers.handle_delete_user({"id": "99", "token": "another-token-123"}) == (404, {"error": "not found"})
    finally:
        os.environ.pop("ADMIN_TOKEN", None)


def test_delete_ok_uses_the_configured_token():
    os.environ["ADMIN_TOKEN"] = "tok-" + "x" * 12
    try:
        assert handlers.handle_delete_user({"id": "2", "token": "tok-" + "x" * 12}) == (200, {"deleted": 2})
        assert handlers.handle_get_user({"id": "2"})[0] == 404
        assert handlers.handle_delete_user({"id": "2", "token": "tok-" + "x" * 12})[0] == 404
        assert handlers.handle_get_user({"id": "1"})[0] == 200
    finally:
        os.environ.pop("ADMIN_TOKEN", None)
