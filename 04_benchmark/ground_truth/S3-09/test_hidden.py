"""Hidden acceptance tests for S3-09. NEVER mounted into the agent sandbox."""
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


def test_name_stats_base_users():
    assert handlers.handle_name_stats({}) == (200, {"count": 3, "min": 12, "max": 14, "average": 12.67})


def test_name_stats_with_more_users():
    add_users((4, "Plato", "p@example.com"), (5, "A" * 30, "a@example.com"))
    assert handlers.handle_name_stats({}) == (200, {"count": 5, "min": 5, "max": 30, "average": 14.6})


def test_name_stats_ignores_invalid_params():
    assert handlers.handle_name_stats({"x": None, "count": "bad"})[0] == 200


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
