"""Hidden acceptance tests for S2-08. NEVER mounted into the agent sandbox."""
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


def rank(formula):
    return handlers.handle_rank_users({"formula": formula})


def test_rank_orders_and_scores():
    res = rank("n * 2 + id")
    assert res[0] == 200 and ids(res) == [2, 3, 1]
    assert res[1]["users"][2] == {"id": 1, "name": "Ada Lovelace", "score": 25}
    assert [u["score"] for u in res[1]["users"]] == [30, 27, 25]
    assert ids(rank("id")) == [3, 2, 1]
    assert ids(rank("n")) == [2, 1, 3]
    assert ids(rank("0")) == [1, 2, 3]
    assert ids(rank("(n - 12) * 5")) == [2, 1, 3]
    assert ids(rank("-id")) == [1, 2, 3]
    assert ids(rank("n // 5 + id")) == [3, 2, 1]


def test_rank_division_by_zero_is_invalid():
    assert rank("n // (id - 1)") == (400, {"error": "invalid formula"})
    assert rank("n // 0") == (400, {"error": "invalid formula"})


def test_rank_invalid_formulas():
    for bad in ("", "  ", "n ** 2", "name", "len('x')", "__import__('os')", "id +", "1.5 * n", "n % 2", "id and n", "n / 2",
                "id; 1", "(id", "id)", "ID", "x", "idn", "id n", 5, None, ["id"]):
        assert rank(bad) == (400, {"error": "invalid formula"}), bad


def test_rank_absent_and_length_limit():
    assert handlers.handle_rank_users({}) == (400, {"error": "invalid formula"})
    ok = "id" + "+id" * 19 + " "
    assert len(ok) == 60 and rank(ok)[0] == 200 and rank(ok)[1]["users"][0]["score"] == 60
    assert rank(ok + " ") == (400, {"error": "invalid formula"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
