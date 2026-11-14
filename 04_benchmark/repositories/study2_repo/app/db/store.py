"""SQLite persistence for users."""

import sqlite3

_conn = sqlite3.connect(":memory:", check_same_thread=False)
_conn.row_factory = sqlite3.Row
_conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE)")
_conn.executemany("INSERT INTO users (id, name, email) VALUES (?, ?, ?)", [
    (1, "Ada Lovelace", "ada@example.com"),
    (2, "Linus Torvalds", "linus@example.com"),
    (3, "Grace Hopper", "grace@example.com"),
])
_conn.commit()


def _to_dict(row):
    return dict(row) if row else None


def get_by_id(user_id: int) -> dict | None:
    return _to_dict(_conn.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone())


def find_by_email(email: str) -> dict | None:
    return _to_dict(_conn.execute("SELECT id, name, email FROM users WHERE email = ?", (email,)).fetchone())
