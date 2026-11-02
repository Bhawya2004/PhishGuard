import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "phishguard.db"

# columns added by the LLM layer (older databases are upgraded automatically)
NEW_COLUMNS = {
    "url_score": "REAL",
    "text_risk": "REAL",
    "llm_summary": "TEXT",
    "llm_fields": "TEXT",
}


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
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
                created_at TEXT, reviewed_at TEXT,
                url_score REAL, text_risk REAL, llm_summary TEXT, llm_fields TEXT
            )
        """)
        existing = {r["name"] for r in c.execute("PRAGMA table_info(emails)").fetchall()}
        for col, typ in NEW_COLUMNS.items():
            if col not in existing:
                c.execute(f"ALTER TABLE emails ADD COLUMN {col} {typ}")


def add_email(sender, subject, body, url, score, reasons, status, true_label, processing_ms,
              url_score=None, text_risk=None, llm_summary=None, llm_fields=None):
    with _conn() as c:
        cur = c.execute(
            """INSERT INTO emails (sender, subject, body, url, score, reasons, status,
               true_label, processing_ms, created_at, url_score, text_risk, llm_summary, llm_fields)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (sender, subject, body, url, score, "; ".join(reasons), status,
             true_label, processing_ms, datetime.now().isoformat(timespec="seconds"),
             url_score, text_risk, llm_summary, llm_fields),
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