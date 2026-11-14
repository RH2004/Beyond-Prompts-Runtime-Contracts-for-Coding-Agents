"""Hidden acceptance tests for S3-10. NEVER mounted into the agent sandbox."""
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


def test_next_id():
    assert handlers.handle_next_id({}) == (200, {"next_id": 4})
    add_users((10, "Zed", "z@example.com"))
    assert handlers.handle_next_id({}) == (200, {"next_id": 11})


def test_next_id_ignores_invalid_params():
    assert handlers.handle_next_id({"x": [1], "id": None}) == (200, {"next_id": 4})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
