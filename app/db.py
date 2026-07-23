"""SQLite storage. One file, no server, safe for thousands of clients.

Schema notes:
  clients.phone      - WhatsApp sender ID (E.164 without '+'), the natural key
  clients.state      - where the conversation is: a question key, or a lifecycle marker
  clients.status     - in_progress | complete
  clients.admin_*    - the follow-up pipeline administrators work from
  messages.wa_id     - Meta's message ID, UNIQUE so webhook retries can't double-process
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator, Optional

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    phone         TEXT    NOT NULL UNIQUE,
    name          TEXT,
    plan_title    TEXT,
    state         TEXT    NOT NULL,
    status        TEXT    NOT NULL DEFAULT 'in_progress',
    admin_status  TEXT    NOT NULL DEFAULT 'new',
    admin_notes   TEXT,
    log_path      TEXT,
    created_at    TEXT    NOT NULL,
    updated_at    TEXT    NOT NULL,
    completed_at  TEXT,
    contacted_at  TEXT,
    off_hours_stage     TEXT NOT NULL DEFAULT 'none',
    off_hours_stage_at  TEXT,
    last_seen_at        TEXT,
    pending_state        TEXT
);

CREATE TABLE IF NOT EXISTS off_hours_contacts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    phone        TEXT    NOT NULL,
    name         TEXT,
    contacted_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS answers (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id     INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    question_key  TEXT    NOT NULL,
    question_text TEXT    NOT NULL,
    raw_answer    TEXT    NOT NULL,
    parsed_value  TEXT,
    answered_at   TEXT    NOT NULL,
    UNIQUE(client_id, question_key)
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id  INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    wa_id      TEXT    UNIQUE,
    direction  TEXT    NOT NULL,
    body       TEXT    NOT NULL,
    created_at TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status, admin_status);
CREATE INDEX IF NOT EXISTS idx_answers_client ON answers(client_id);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(config.DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        # Migrate columns added after the original schema - CREATE TABLE IF NOT
        # EXISTS above only applies to brand-new databases, not existing ones.
        for ddl in (
            "ALTER TABLE clients ADD COLUMN off_hours_stage TEXT NOT NULL DEFAULT 'none'",
            "ALTER TABLE clients ADD COLUMN off_hours_stage_at TEXT",
            "ALTER TABLE clients ADD COLUMN last_seen_at TEXT",
            "ALTER TABLE clients ADD COLUMN pending_state TEXT",
        ):
            try:
                conn.execute(ddl)
            except sqlite3.OperationalError as exc:
                if "duplicate column" not in str(exc).lower():
                    raise


# --- clients -------------------------------------------------------------


def get_client(phone: str) -> Optional[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM clients WHERE phone = ?", (phone,)
        ).fetchone()


def create_client(phone: str, state: str) -> sqlite3.Row:
    ts = now()
    with connect() as conn:
        conn.execute(
            "INSERT INTO clients (phone, state, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (phone, state, ts, ts),
        )
    client = get_client(phone)
    assert client is not None
    return client


def update_client(phone: str, **fields: Any) -> None:
    if not fields:
        return
    fields["updated_at"] = now()
    assignments = ", ".join(f"{k} = ?" for k in fields)
    with connect() as conn:
        conn.execute(
            f"UPDATE clients SET {assignments} WHERE phone = ?",
            (*fields.values(), phone),
        )


# --- answers -------------------------------------------------------------


def save_answer(
    client_id: int,
    question_key: str,
    question_text: str,
    raw_answer: str,
    parsed_value: str,
) -> None:
    """Upsert - re-answering a question overwrites the previous value."""
    with connect() as conn:
        conn.execute(
            "INSERT INTO answers "
            "(client_id, question_key, question_text, raw_answer, parsed_value, answered_at) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(client_id, question_key) DO UPDATE SET "
            "raw_answer = excluded.raw_answer, "
            "parsed_value = excluded.parsed_value, "
            "answered_at = excluded.answered_at",
            (client_id, question_key, question_text, raw_answer, parsed_value, now()),
        )


def get_answers(client_id: int) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM answers WHERE client_id = ? ORDER BY id", (client_id,)
        ).fetchall()


# --- off-hours contact log ------------------------------------------------


def log_off_hours_contact(phone: str, name: Optional[str]) -> None:
    """Record every off-hours contact for callback follow-up, one row per message."""
    with connect() as conn:
        conn.execute(
            "INSERT INTO off_hours_contacts (phone, name, contacted_at) VALUES (?, ?, ?)",
            (phone, name, now()),
        )


def list_off_hours_contacts() -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM off_hours_contacts ORDER BY contacted_at DESC"
        ).fetchall()


# --- messages ------------------------------------------------------------


def already_processed(wa_id: str) -> bool:
    """Meta retries webhooks. Returns True if we've already seen this message ID."""
    with connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM messages WHERE wa_id = ?", (wa_id,)
        ).fetchone()
    return row is not None


def log_message(
    client_id: Optional[int], direction: str, body: str, wa_id: Optional[str] = None
) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO messages (client_id, wa_id, direction, body, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (client_id, wa_id, direction, body, now()),
        )
