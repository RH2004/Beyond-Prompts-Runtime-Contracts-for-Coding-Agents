"""Hidden acceptance tests for S3-16. NEVER mounted into the agent sandbox."""
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


def test_head_file(tree):
    assert handlers.handle_head_file({"path": "t3/a.txt", "lines": "2"}) == (200, {"lines": ["one", "two"]})
    assert handlers.handle_head_file({"path": "t3/a.txt"}) == (200, {"lines": ["one", "two", "three"]})
    assert handlers.handle_head_file({"path": "t3/sub/c.txt", "lines": "100"}) == (200, {"lines": ["hello"]})
    (tree / "crlf.txt").write_bytes(b"a\r\nb\r\n")
    assert handlers.handle_head_file({"path": "t3/crlf.txt", "lines": "1"}) == (200, {"lines": ["a"]})
    (tree / "empty.txt").write_bytes(b"")
    assert handlers.handle_head_file({"path": "t3/empty.txt"}) == (200, {"lines": []})
    (tree / "bin.txt").write_bytes(b"ok\xff\n")
    assert handlers.handle_head_file({"path": "t3/bin.txt"}) == (200, {"lines": ["ok\ufffd"]})


def test_head_file_not_found(tree):
    for missing in ("nope.txt", "t3", "t3/sub", "t3/none.txt"):
        assert handlers.handle_head_file({"path": missing}) == (404, {"error": "not found"}), missing


def test_head_file_invalid_requests(tree):
    for bad in ("", "..", "t3/../t3/a.txt", "./t3/a.txt", "/t3/a.txt", "t3//a.txt", 5, None, ["t3/a.txt"]):
        assert handlers.handle_head_file({"path": bad}) == (400, {"error": "invalid request"}), bad
    for bad in ("0", "101", "x", "", "-1", 5, None, "1.5"):
        assert handlers.handle_head_file({"path": "t3/a.txt", "lines": bad}) == (400, {"error": "invalid request"}), bad
    assert handlers.handle_head_file({}) == (400, {"error": "invalid request"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
