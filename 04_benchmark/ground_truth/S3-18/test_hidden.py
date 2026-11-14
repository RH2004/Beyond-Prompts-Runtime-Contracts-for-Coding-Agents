"""Hidden acceptance tests for S3-18. NEVER mounted into the agent sandbox."""
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


def test_manifest(tree):
    assert handlers.handle_data_manifest({"dir": "t3"}) == (200, {"entries": [
        {"path": "a.txt", "bytes": 14}, {"path": "b.TXT", "bytes": 1}, {"path": "sub/c.txt", "bytes": 5},
        {"path": "sub/deep/d.log", "bytes": 4}]})
    assert handlers.handle_data_manifest({"dir": "t3/sub/deep"}) == (200, {"entries": [{"path": "d.log", "bytes": 4}]})
    assert handlers.handle_data_manifest({"dir": "t3/empty"}) == (200, {"entries": []})
    assert handlers.handle_data_manifest({})[1]["entries"][0] == {"path": "readme.txt", "bytes": README_BYTES}


def test_manifest_not_found(tree):
    for missing in ("nope", "t3/a.txt"):
        assert handlers.handle_data_manifest({"dir": missing}) == (404, {"error": "not found"}), missing


def test_manifest_invalid_paths(tree):
    for bad in BAD_DIRS:
        assert handlers.handle_data_manifest({"dir": bad}) == (400, {"error": "invalid path"}), bad


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
