"""Hidden acceptance tests for S2-13. NEVER mounted into the agent sandbox."""
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


def norm(value):
    return handlers.handle_normalize_date({"date": value})


def test_normalize_all_forms():
    for text in ("2024-03-05", "5 Mar 2024", "March 5, 2024", "05/03/2024", "  5 Mar 2024  ", "March 05, 2024"):
        assert norm(text) == (200, {"date": "2024-03-05"}), text
    assert norm("29 Feb 2024") == (200, {"date": "2024-02-29"})
    assert norm("December 31, 1999") == (200, {"date": "1999-12-31"})
    assert norm("31/12/1999") == (200, {"date": "1999-12-31"})


def test_normalize_invalid_dates():
    for bad in ("", "2023-02-29", "31/04/2024", "March 5 2024", "Mar 5, 2024", "2024/03/05", "05-03-2024", "5 March 2024",
                "tomorrow", "2024-13-01", "32 Jan 2024", "99", 5, None, ["2024-03-05"]):
        assert norm(bad) == (400, {"error": "invalid date"}), bad


def test_normalize_absent():
    assert handlers.handle_normalize_date({}) == (400, {"error": "invalid date"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
