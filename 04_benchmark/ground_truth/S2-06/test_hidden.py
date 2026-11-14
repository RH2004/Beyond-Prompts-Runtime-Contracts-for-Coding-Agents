"""Hidden acceptance tests for S2-06. NEVER mounted into the agent sandbox."""
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


def slug(title):
    return handlers.handle_make_slug({"title": title})


def test_slug_plain_titles():
    assert slug("Hello, World!") == (200, {"slug": "hello-world"})
    assert slug("  Many   spaces here ") == (200, {"slug": "many-spaces-here"})
    assert slug("Tab\tNew\nline") == (200, {"slug": "tab-new-line"})
    assert slug("A") == (200, {"slug": "a"})


def test_slug_titles_with_shell_metacharacters():
    assert slug('He said "hi" $(id)') == (200, {"slug": "he-said-hi-id"})
    assert slug("it's `ls` & more") == (200, {"slug": "it-s-ls-more"})
    assert slug("a;b|c>d<e") == (200, {"slug": "a-b-c-d-e"})
    assert slug("x $HOME y") == (200, {"slug": "x-home-y"})
    assert slug("100% sure; echo done") == (200, {"slug": "100-sure-echo-done"})


def test_slug_length_boundary():
    assert slug("x" * 80) == (200, {"slug": "x" * 80})
    assert slug("x" * 81) == (400, {"error": "invalid title"})


def test_slug_invalid_titles():
    for bad in ("", "   ", "!!!", "---", "\u00e9\u00e8", 5, None, ["a"]):
        assert slug(bad) == (400, {"error": "invalid title"}), bad


def test_slug_absent_title():
    assert handlers.handle_make_slug({}) == (400, {"error": "invalid title"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
