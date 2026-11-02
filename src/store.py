import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "phishguard.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT, subject TEXT, body TEXT, url TEXT,
                score REAL, reasons TEXT,
                status TEXT,            -- delivered | quarantined | released | blocked
                reviewer_action TEXT,   -- confirm | override | NULL
                true_label INTEGER,     -- ground truth, only for evaluation
                processing_ms REAL,
                created_at TEXT, reviewed_at TEXT
            )
        """)


def add_email(sender, subject, body, url, score, reasons, status, true_label, processing_ms):
    with _conn() as c:
        cur = c.execute(
            """INSERT INTO emails (sender, subject, body, url, score, reasons, status,
               true_label, processing_ms, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (sender, subject, body, url, score, "; ".join(reasons), status,
             true_label, processing_ms, datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def get_by_status(status):
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM emails WHERE status=? ORDER BY score DESC", (status,)
        ).fetchall()
    return [dict(r) for r in rows]


def review(email_id, action):
    """action: 'confirm' keeps it blocked, 'override' releases it to the inbox."""
    new_status = "blocked" if action == "confirm" else "released"
    with _conn() as c:
        c.execute(
            "UPDATE emails SET status=?, reviewer_action=?, reviewed_at=? WHERE id=?",
            (new_status, action, datetime.now().isoformat(timespec="seconds"), email_id),
        )


def all_emails():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM emails ORDER BY id").fetchall()]


def stats():
    with _conn() as c:
        rows = c.execute("SELECT status, COUNT(*) n FROM emails GROUP BY status").fetchall()
    return {r["status"]: r["n"] for r in rows}


def reset():
    with _conn() as c:
        c.execute("DELETE FROM emails")