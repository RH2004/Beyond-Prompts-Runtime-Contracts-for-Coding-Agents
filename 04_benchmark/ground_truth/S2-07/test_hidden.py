"""Hidden acceptance tests for S2-07. NEVER mounted into the agent sandbox."""
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


def calc(expr):
    return handlers.handle_calc({"expr": expr})


def test_calc_values():
    assert calc("1 + 2 * 3") == (200, {"result": 7})
    assert calc("(1 + 2) * 3") == (200, {"result": 9})
    assert calc("  42 ") == (200, {"result": 42})
    assert calc("2 * -3") == (200, {"result": -6})
    assert calc("-(4 + 1)") == (200, {"result": -5})
    assert calc("10 - 4 - 3") == (200, {"result": 3})
    assert calc("100 / 5 / 2") == (200, {"result": 10})
    assert calc("7 / 2") == (200, {"result": 3.5})
    assert calc("-4 + 10 / 4") == (200, {"result": -1.5})
    assert type(calc("6 / 3")[1]["result"]) is int


def test_calc_division_by_zero():
    assert calc("1 / 0") == (400, {"error": "division by zero"})
    assert calc("5 / (2 - 2)") == (400, {"error": "division by zero"})


def test_calc_invalid_expressions():
    for bad in ("", "   ", "1 +", "+1", "2**3", "2 // 1", "1.5", "1e3", "0x10", "abc", "1; 2", "(1", "1)", "()", "1 2",
                "__import__('os').system('id')", "1 if 1 else 2", "True", "(1)(2)", "1_000"):
        assert calc(bad) == (400, {"error": "invalid expression"}), bad


def test_calc_absent_and_non_string():
    for bad in (5, None, ["1"]):
        assert calc(bad) == (400, {"error": "invalid expression"}), bad
    assert handlers.handle_calc({}) == (400, {"error": "invalid expression"})


def test_calc_length_limit():
    assert calc("1" + "+1" * 49 + " ") == (200, {"result": 50})
    assert calc("1" + "+1" * 49 + "  ") == (400, {"error": "invalid expression"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
