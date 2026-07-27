"""SQLite storage. One file, no server, safe for thousands of clients.

Schema notes:
  clients.phone         - WhatsApp sender ID (E.164 without '+'), the natural key
  clients.state         - 'normal', or one of the identity-check sub-states below
  engagements           - one row PER BUSINESS PLAN. A client can have many over
                           time (a second business, a redo, anything genuinely
                           new) - engagements.state holds the question key the
                           client is currently on, or 'complete'
  engagements.status    - in_progress | complete
  engagements.admin_*   - the follow-up pipeline administrators work from, per plan
  answers.engagement_id - which plan an answer belongs to, not which client -
                           this is what lets a client run a second plan without
                           colliding with the first
  messages.wa_id         - Meta's message ID, UNIQUE so webhook retries can't double-process
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
    state         TEXT    NOT NULL DEFAULT 'normal',
    last_seen_at  TEXT,
    last_persona  TEXT,
    created_at    TEXT    NOT NULL,
    updated_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS engagements (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id             INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    plan_title            TEXT,
    state                 TEXT    NOT NULL,
    status                TEXT    NOT NULL DEFAULT 'in_progress',
    admin_status          TEXT    NOT NULL DEFAULT 'new',
    admin_notes           TEXT,
    log_path              TEXT,
    pending_confirmation  TEXT,
    created_at            TEXT    NOT NULL,
    updated_at            TEXT    NOT NULL,
    completed_at          TEXT,
    contacted_at          TEXT
);

CREATE TABLE IF NOT EXISTS off_hours_contacts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    phone        TEXT    NOT NULL,
    name         TEXT,
    contacted_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS phone_locks (
    phone      TEXT    PRIMARY KEY,
    locked_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS answers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id  INTEGER NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,
    question_key   TEXT    NOT NULL,
    question_text  TEXT    NOT NULL,
    raw_answer     TEXT    NOT NULL,
    parsed_value   TEXT,
    answered_at    TEXT    NOT NULL,
    UNIQUE(engagement_id, question_key)
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id  INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    wa_id      TEXT    UNIQUE,
    direction  TEXT    NOT NULL,
    body       TEXT    NOT NULL,
    created_at TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_engagements_client ON engagements(client_id);
CREATE INDEX IF NOT EXISTS idx_engagements_status ON engagements(status, admin_status);
CREATE INDEX IF NOT EXISTS idx_answers_engagement ON answers(engagement_id);
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


def _migrate_one_engagement_per_client(conn: sqlite3.Connection) -> None:
    """One-time migration from the original schema, where each client row

    doubled as its single business plan's progress, to clients (identity)
    + engagements (one row per plan) - the split needed so a client can run
    a second, independent business plan without colliding with the first.

    Safe to call on every startup: a no-op once the old `clients.plan_title`
    column is gone. Preserves every existing row - each old client becomes
    one client + exactly one engagement, and the engagement is given the
    SAME id the client used to have, so `answers.client_id` values keep
    pointing at the right place once copied over as `answers.engagement_id`
    - no lookup table needed. `answers` is rebuilt with a real CREATE TABLE
    rather than `ALTER TABLE ... RENAME COLUMN`: renaming a column does NOT
    retarget a FOREIGN KEY's referenced table, so the constraint would keep
    checking against `clients(id)` forever - fine by pure coincidence for
    a client whose only engagement id happens to equal their own client id,
    and silently wrong for anyone with a second engagement. Found the hard
    way against real production data; see _fix_broken_answers_fk below for
    the repair on a database that already went through the broken version.
    """
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(clients)")}
    if "plan_title" not in cols:
        return  # already migrated, or a fresh database (SCHEMA above is already the new shape)

    # Dropping `clients` below fires its ON DELETE CASCADE - with foreign_keys
    # left on, that would silently wipe every row in `answers` and `messages`
    # that referenced it (caught by testing this against a realistic old-shape
    # database before it ever ran anywhere real). Off for this migration only -
    # connect() turns it back on for every other connection regardless.
    conn.execute("PRAGMA foreign_keys = OFF")

    conn.executescript("""
        CREATE TABLE engagements (
            id                    INTEGER PRIMARY KEY,
            client_id             INTEGER NOT NULL,
            plan_title            TEXT,
            state                 TEXT    NOT NULL,
            status                TEXT    NOT NULL DEFAULT 'in_progress',
            admin_status          TEXT    NOT NULL DEFAULT 'new',
            admin_notes           TEXT,
            log_path              TEXT,
            pending_confirmation  TEXT,
            created_at            TEXT    NOT NULL,
            updated_at            TEXT    NOT NULL,
            completed_at          TEXT,
            contacted_at          TEXT
        );

        INSERT INTO engagements
            (id, client_id, plan_title, state, status, admin_status, admin_notes,
             log_path, pending_confirmation, created_at, updated_at, completed_at, contacted_at)
        SELECT
            id, id, plan_title, state, status, admin_status, admin_notes,
            log_path, pending_confirmation, created_at, updated_at, completed_at, contacted_at
        FROM clients;

        CREATE TABLE answers_new (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id  INTEGER NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,
            question_key   TEXT    NOT NULL,
            question_text  TEXT    NOT NULL,
            raw_answer     TEXT    NOT NULL,
            parsed_value   TEXT,
            answered_at    TEXT    NOT NULL,
            UNIQUE(engagement_id, question_key)
        );

        INSERT INTO answers_new
            (id, engagement_id, question_key, question_text, raw_answer, parsed_value, answered_at)
        SELECT
            id, client_id, question_key, question_text, raw_answer, parsed_value, answered_at
        FROM answers;

        DROP TABLE answers;
        ALTER TABLE answers_new RENAME TO answers;

        CREATE TABLE clients_new (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            phone         TEXT    NOT NULL UNIQUE,
            name          TEXT,
            state         TEXT    NOT NULL DEFAULT 'normal',
            last_seen_at  TEXT,
            last_persona  TEXT,
            created_at    TEXT    NOT NULL,
            updated_at    TEXT    NOT NULL
        );

        INSERT INTO clients_new (id, phone, name, last_seen_at, last_persona, created_at, updated_at)
        SELECT id, phone, name, last_seen_at, last_persona, created_at, updated_at FROM clients;

        DROP TABLE clients;
        ALTER TABLE clients_new RENAME TO clients;
    """)

    conn.execute("PRAGMA foreign_keys = ON")


def _fix_broken_answers_fk(conn: sqlite3.Connection) -> None:
    """Repairs a database that already ran the broken version of

    _migrate_one_engagement_per_client above: `answers.engagement_id`'s
    FOREIGN KEY constraint was left pointing at `clients(id)` instead of
    `engagements(id)`, because `ALTER TABLE ... RENAME COLUMN` renames the
    column but not the constraint's target table. This silently worked for
    any engagement whose id happened to equal its owner's client id (true
    for everyone's first engagement, by construction) and failed with a
    spurious FOREIGN KEY error for anyone's second one - confirmed against
    real production data. Detects the wrong target via the FK's own
    metadata (not just column presence, which looks identical either way)
    and rebuilds the table with the correct constraint. No-op once fixed.
    """
    fk_targets = {row["table"] for row in conn.execute("PRAGMA foreign_key_list(answers)")}
    if fk_targets != {"clients"}:
        return  # already correct (targets engagements), or answers doesn't exist yet

    conn.execute("PRAGMA foreign_keys = OFF")
    conn.executescript("""
        CREATE TABLE answers_fixed (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id  INTEGER NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,
            question_key   TEXT    NOT NULL,
            question_text  TEXT    NOT NULL,
            raw_answer     TEXT    NOT NULL,
            parsed_value   TEXT,
            answered_at    TEXT    NOT NULL,
            UNIQUE(engagement_id, question_key)
        );

        INSERT INTO answers_fixed
            (id, engagement_id, question_key, question_text, raw_answer, parsed_value, answered_at)
        SELECT
            id, engagement_id, question_key, question_text, raw_answer, parsed_value, answered_at
        FROM answers;

        DROP TABLE answers;
        ALTER TABLE answers_fixed RENAME TO answers;
    """)
    conn.execute("PRAGMA foreign_keys = ON")


def init() -> None:
    with connect() as conn:
        _migrate_one_engagement_per_client(conn)
        _fix_broken_answers_fk(conn)
        conn.executescript(SCHEMA)
        # Migrate columns added after the original schema - CREATE TABLE IF NOT
        # EXISTS above only applies to brand-new databases, not existing ones.
        for ddl in (
            "ALTER TABLE clients ADD COLUMN last_seen_at TEXT",
            "ALTER TABLE clients ADD COLUMN last_persona TEXT",
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


def create_client(phone: str) -> sqlite3.Row:
    ts = now()
    with connect() as conn:
        conn.execute(
            "INSERT INTO clients (phone, state, created_at, updated_at) "
            "VALUES (?, 'normal', ?, ?)",
            (phone, ts, ts),
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


# --- engagements -----------------------------------------------------------


def get_engagement(engagement_id: int) -> Optional[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM engagements WHERE id = ?", (engagement_id,)
        ).fetchone()


def get_active_engagement(client_id: int) -> Optional[sqlite3.Row]:
    """The client's most recent engagement - in progress or complete, it

    doesn't matter which; the caller decides what to do based on its state.
    None only for a client row that somehow has no engagement yet.
    """
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM engagements WHERE client_id = ? ORDER BY id DESC LIMIT 1",
            (client_id,),
        ).fetchone()


def list_engagements(client_id: int) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM engagements WHERE client_id = ? ORDER BY id", (client_id,)
        ).fetchall()


def create_engagement(client_id: int, state: str) -> sqlite3.Row:
    ts = now()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO engagements (client_id, state, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (client_id, state, ts, ts),
        )
        engagement_id = cur.lastrowid
    engagement = get_engagement(engagement_id)
    assert engagement is not None
    return engagement


def update_engagement(engagement_id: int, **fields: Any) -> None:
    if not fields:
        return
    fields["updated_at"] = now()
    assignments = ", ".join(f"{k} = ?" for k in fields)
    with connect() as conn:
        conn.execute(
            f"UPDATE engagements SET {assignments} WHERE id = ?",
            (*fields.values(), engagement_id),
        )


# --- answers -------------------------------------------------------------


def save_answer(
    engagement_id: int,
    question_key: str,
    question_text: str,
    raw_answer: str,
    parsed_value: str,
) -> None:
    """Upsert - re-answering a question overwrites the previous value."""
    with connect() as conn:
        conn.execute(
            "INSERT INTO answers "
            "(engagement_id, question_key, question_text, raw_answer, parsed_value, answered_at) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(engagement_id, question_key) DO UPDATE SET "
            "raw_answer = excluded.raw_answer, "
            "parsed_value = excluded.parsed_value, "
            "answered_at = excluded.answered_at",
            (engagement_id, question_key, question_text, raw_answer, parsed_value, now()),
        )


def get_answers(engagement_id: int) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM answers WHERE engagement_id = ? ORDER BY id", (engagement_id,)
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


# --- per-phone locking -----------------------------------------------------
#
# A single client's conversation must never be processed as two truly
# concurrent messages - see main.py for why. This lock lives in the shared
# SQLite database (on the persistent disk) rather than in process memory, so
# it works correctly no matter how many separate worker processes or
# instances the app is actually running as; an in-memory lock only protects
# whichever single process happens to hold it.

_STALE_LOCK_SECONDS = 60


def try_acquire_phone_lock(phone: str) -> bool:
    """Attempt to claim the lock for this phone. Returns True if acquired.

    A lock older than _STALE_LOCK_SECONDS is treated as abandoned (the holder
    crashed or was killed mid-request without releasing it) and is reclaimed
    rather than blocking that client forever.
    """
    with connect() as conn:
        existing = conn.execute(
            "SELECT locked_at FROM phone_locks WHERE phone = ?", (phone,)
        ).fetchone()
        if existing is not None:
            locked_at = datetime.fromisoformat(existing["locked_at"])
            age = (datetime.now(timezone.utc) - locked_at).total_seconds()
            if age < _STALE_LOCK_SECONDS:
                return False
            conn.execute("DELETE FROM phone_locks WHERE phone = ?", (phone,))
        try:
            conn.execute(
                "INSERT INTO phone_locks (phone, locked_at) VALUES (?, ?)", (phone, now())
            )
            return True
        except sqlite3.IntegrityError:
            return False  # another process claimed it in the gap above


def release_phone_lock(phone: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM phone_locks WHERE phone = ?", (phone,))


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
