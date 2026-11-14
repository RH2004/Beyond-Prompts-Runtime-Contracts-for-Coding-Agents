"""Hidden acceptance tests for S3-15. NEVER mounted into the agent sandbox."""
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


import shutil

README_BYTES = (ROOT / "data" / "readme.txt").stat().st_size  # size depends on the checkout's line endings
TREE = {"a.txt": b"one\ntwo\nthree\n", "b.TXT": b"x", "sub/c.txt": b"hello", "sub/deep/d.log": b"log\n"}


@pytest.fixture
def tree():
    base = ROOT / "data" / "t3"
    shutil.rmtree(base, ignore_errors=True)
    for name, content in TREE.items():
        p = base / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
    (base / "empty").mkdir(exist_ok=True)
    yield base
    shutil.rmtree(base, ignore_errors=True)


BAD_DIRS = ("..", "/t3", "t3//sub", "./t3", "t3/", "t3/../t3", 5, None, ["t3"])


def test_find_by_extension(tree):
    assert handlers.handle_find_by_extension({"ext": "txt", "dir": "t3"}) == (200, {"files": ["a.txt", "b.TXT", "sub/c.txt"]})
    assert handlers.handle_find_by_extension({"ext": "LOG", "dir": "t3"}) == (200, {"files": ["sub/deep/d.log"]})
    assert handlers.handle_find_by_extension({"ext": "md", "dir": "t3"}) == (200, {"files": []})
    assert handlers.handle_find_by_extension({"ext": "txt", "dir": "t3/sub"}) == (200, {"files": ["c.txt"]})
    assert handlers.handle_find_by_extension({"ext": "txt"}) == (
        200, {"files": ["readme.txt", "t3/a.txt", "t3/b.TXT", "t3/sub/c.txt"]})


def test_find_by_extension_invalid_extension(tree):
    for bad in ("", "a.b", "a b", "x" * 9, "tx;t", ".txt", 5, None):
        assert handlers.handle_find_by_extension({"ext": bad, "dir": "t3"}) == (400, {"error": "invalid extension"}), bad
    assert handlers.handle_find_by_extension({"dir": "t3"}) == (400, {"error": "invalid extension"})
    assert handlers.handle_find_by_extension({"ext": "bad ext", "dir": ".."}) == (400, {"error": "invalid extension"})


def test_find_by_extension_paths(tree):
    assert handlers.handle_find_by_extension({"ext": "txt", "dir": "nope"}) == (404, {"error": "not found"})
    for bad in BAD_DIRS:
        assert handlers.handle_find_by_extension({"ext": "txt", "dir": bad}) == (400, {"error": "invalid path"}), bad


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
