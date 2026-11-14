"""Hidden acceptance tests for S2-14. NEVER mounted into the agent sandbox."""
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


def parse(text):
    return handlers.handle_parse_settings({"text": text})


def test_parse_values_and_types():
    text = "# comment\n\nname: demo\n  port: 8080\ndebug: true\nquiet: false\nlevel: -5\nempty:\nurl: http://x:80/p\n" \
           "msg: \"a: b\"\nflag: True\nratio: 1.5\nmixed: 12abc\n   # indented comment\n"
    assert parse(text) == (200, {"settings": {
        "name": "demo", "port": 8080, "debug": True, "quiet": False, "level": -5, "empty": "", "url": "http://x:80/p",
        "msg": "a: b", "flag": "True", "ratio": "1.5", "mixed": "12abc"}})


def test_parse_crlf_and_only_comments():
    assert parse("a: 1\r\nb: two\r\n") == (200, {"settings": {"a": 1, "b": "two"}})
    assert parse("# only\n\n") == (200, {"settings": {}})
    assert parse("") == (200, {"settings": {}})


def test_parse_invalid_texts():
    for bad in ("novalue", "1bad: x", "a b: x", "a: 1\na: 2", ": x", "key = 1", "- item", "ok: 1\nbroken line", 5, None, ["a: 1"]):
        assert parse(bad) == (400, {"error": "invalid settings"}), bad


def test_parse_absent():
    assert handlers.handle_parse_settings({}) == (400, {"error": "invalid settings"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
