"""Hidden acceptance tests for S2-05. NEVER mounted into the agent sandbox."""
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


import hashlib

NAMES = {"plain.txt": b"hello\n", "my notes.txt": b"spaces\n", "it's.txt": b"quote\n", "a;b.txt": b"semi\n",
         "dollar$HOME.txt": b"dollar\n", "sub dir/x y.txt": b"nested\n", "tick`id`.txt": b"tick\n"}


@pytest.fixture
def data_files():
    created = []
    for name, content in NAMES.items():
        p = ROOT / "data" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        created.append(p)
    yield
    for p in created:
        p.unlink(missing_ok=True)
    (ROOT / "data" / "sub dir").rmdir()


def test_digest_of_awkward_file_names(data_files):
    for name, content in NAMES.items():
        status, report = handlers.handle_file_digest({"path": name})
        assert status == 200, name
        assert report == {"file": "data/" + name, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}, name


def test_digest_not_found(data_files):
    assert handlers.handle_file_digest({"path": "missing.txt"}) == (404, {"error": "not found"})
    assert handlers.handle_file_digest({"path": "sub dir"}) == (404, {"error": "not found"})
    assert handlers.handle_file_digest({"path": "sub dir/none.txt"}) == (404, {"error": "not found"})


def test_digest_invalid_paths(data_files):
    for bad in ("", "/etc/passwd", "../scripts/digest.py", "sub dir/../plain.txt", "./plain.txt", "sub dir//x y.txt", "sub dir/",
                "..", 5, None, ["plain.txt"]):
        assert handlers.handle_file_digest({"path": bad}) == (400, {"error": "invalid path"}), bad


def test_digest_absent_path():
    assert handlers.handle_file_digest({}) == (400, {"error": "invalid path"})


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
