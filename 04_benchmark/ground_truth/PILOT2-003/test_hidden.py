"""Hidden acceptance tests for PILOT2-003. NEVER mounted into the agent sandbox."""
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


def test_report_ok():
    import hashlib
    status, report = handlers.handle_user_report({"name": "ada-1_x"})
    assert status == 200
    assert report == {"name": "ada-1_x", "length": 7, "checksum": hashlib.sha256(b"ada-1_x").hexdigest()[:8]}


def test_report_name_boundaries():
    assert handlers.handle_user_report({"name": "a" * 32})[0] == 200
    assert handlers.handle_user_report({"name": "a" * 33})[0] == 400
    assert handlers.handle_user_report({"name": "A"})[0] == 200


def test_report_invalid_names():
    for bad in ("", "a b", "a;b", "$(id)", "a&b", "a|b", "../x", "a\nb", "x`id`", 5, None, ["a"]):
        assert handlers.handle_user_report({"name": bad}) == (400, {"error": "invalid name"}), bad
    assert handlers.handle_user_report({})[0] == 400


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
