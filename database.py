import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path

from config import SQLITE_PATH as SQLITE_PATH_RAW

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_items_owner_id ON items(owner_id);
"""

_connection_factory: Callable[[], sqlite3.Connection] | None = None


def sqlite_path(url: str) -> str:
    """Map a sqlite URL or filesystem path to a sqlite3 connect target."""
    raw = url.strip()
    if raw in {":memory:", "sqlite://", "sqlite:///:memory:"}:
        return ":memory:"
    if raw.startswith("file:"):
        return raw
    if (
        raw.startswith("postgresql")
        or raw.startswith("postgres")
        or ("://" in raw and not raw.startswith("sqlite"))
    ):
        scheme = raw.split("://", 1)[0]
        raise RuntimeError(
            f"This app uses the sqlite3 stdlib driver and does not support "
            f"{scheme!r} URLs. Set SQLITE_PATH to a file path "
            f"(e.g. ./app.db) or a sqlite URL (e.g. sqlite:///./app.db)."
        )
    if raw.startswith("sqlite:///"):
        return raw.removeprefix("sqlite:///")
    return raw


SQLITE_PATH: str = sqlite_path(SQLITE_PATH_RAW)


def set_connection_factory(factory: Callable[[], sqlite3.Connection] | None) -> None:
    """Replace the default connector (used by tests for a shared in-memory DB)."""
    global _connection_factory
    _connection_factory = factory


def connect(path: str | None = None) -> sqlite3.Connection:
    if _connection_factory is not None:
        return _connection_factory()

    db_path = SQLITE_PATH if path is None else path
    use_uri = db_path.startswith("file:")
    is_memory = db_path == ":memory:" or "mode=memory" in db_path
    if not is_memory and not use_uri:
        parent = Path(db_path).expanduser().parent
        if parent != Path(""):
            parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        db_path,
        check_same_thread=False,
        uri=use_uri,
        timeout=30,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if not is_memory and not use_uri:
        conn.execute("PRAGMA journal_mode = WAL")
    return conn


def get_db() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection | None = None) -> None:
    owns_connection = conn is None
    db = connect() if owns_connection else conn
    try:
        db.executescript(SCHEMA)
        db.commit()
    finally:
        if owns_connection:
            db.close()


def row_to_dict(row: sqlite3.Row) -> dict:
    data = dict(row)
    if "is_active" in data:
        data["is_active"] = bool(data["is_active"])
    return data
