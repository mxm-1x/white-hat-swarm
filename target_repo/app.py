acme-billing — internal customer lookup service (DEMO TARGET).

NOTE: This module ships with a deliberately planted vulnerability so the
White-Hat Remediation Swarm has something real to find, patch, and verify.

Vulnerability: CWE-89 SQL Injection in `get_user_by_name`.
The query is built with an f-string, so attacker-controlled `name` is
concatenated directly into SQL.
"

import sqlite3


def init_db() -> sqlite3.Connection:
    """Create an in-memory DB seeded with a couple of customers."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, is_admin INTEGER)"
    )
    conn.executemany(
        "INSERT INTO users (name, email, is_admin) VALUES (?, ?, ?)",
        [
            ("alice", "alice@acme.test", 0),
            ("bob", "bob@acme.test", 0),
            ("root", "root@acme.test", 1),
        ],
    )
    conn.commit()
    return conn


def get_user_by_name(conn: sqlite3.Connection, name: str):
    """Look up a single user by exact name."""
    query = "SELECT id, name, email, is_admin FROM users WHERE name = ?"
    cur = conn.execute(query, (name,))
    return cur.fetchall()


if __name__ == "__main__":
    db = init_db()
    print("normal lookup ->", get_user_by_name(db, "alice"))
    print("injection     ->", get_user_by_name(db, "x' OR '1'='1"))
