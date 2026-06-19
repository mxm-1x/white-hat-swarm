"""Regression + security tests for acme-billing.

The QA Tester agent runs `pytest` against this file inside a sandbox copy of
the repo. The functional tests must keep passing after the Engineer's patch;
the security test (`test_no_sql_injection`) is the boundary test that FAILS on
the vulnerable code and PASSES once the query is parameterized.
"""

import app


def test_lookup_returns_single_user():
    conn = app.init_db()
    rows = app.get_user_by_name(conn, "alice")
    assert len(rows) == 1
    assert rows[0][1] == "alice"


def test_lookup_unknown_user_returns_nothing():
    conn = app.init_db()
    rows = app.get_user_by_name(conn, "nobody")
    assert rows == []


def test_no_sql_injection():
    """A classic tautology payload must NOT leak every row."""
    conn = app.init_db()
    rows = app.get_user_by_name(conn, "x' OR '1'='1")
    # Vulnerable code returns all 3 users here; patched code returns 0.
    assert rows == [], f"SQL injection leaked {len(rows)} rows"
