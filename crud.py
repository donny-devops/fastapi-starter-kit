import sqlite3

from database import row_to_dict
from schemas import ItemCreate, ItemUpdate, UserCreate, UserUpdate

_USER_UPDATE_FIELDS = frozenset({"name", "email", "is_active"})
_ITEM_UPDATE_FIELDS = frozenset({"title", "description"})


def _require_lastrowid(cursor: sqlite3.Cursor) -> int:
    row_id = cursor.lastrowid
    if row_id is None:
        raise RuntimeError("INSERT did not produce a row id")
    return row_id


def get_user(db: sqlite3.Connection, user_id: int) -> dict | None:
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_dict(row) if row else None


def get_user_by_email(db: sqlite3.Connection, email: str) -> dict | None:
    row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return row_to_dict(row) if row else None


def get_users(db: sqlite3.Connection, skip: int = 0, limit: int = 100) -> list[dict]:
    rows = db.execute(
        "SELECT * FROM users ORDER BY id LIMIT ? OFFSET ?",
        (limit, skip),
    ).fetchall()
    return [row_to_dict(row) for row in rows]


def create_user(db: sqlite3.Connection, data: UserCreate) -> dict:
    try:
        cursor = db.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            (data.name, data.email),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise
    user = get_user(db, _require_lastrowid(cursor))
    if user is None:
        raise RuntimeError("Failed to load user after insert")
    return user


def update_user(db: sqlite3.Connection, user_id: int, data: UserUpdate) -> dict | None:
    if get_user(db, user_id) is None:
        return None
    fields = {
        key: (int(value) if key == "is_active" and value is not None else value)
        for key, value in data.model_dump(exclude_unset=True).items()
        if key in _USER_UPDATE_FIELDS
    }
    if fields:
        assignments = ", ".join(f"{column} = ?" for column in fields)
        try:
            db.execute(
                f"UPDATE users SET {assignments} WHERE id = ?",  # noqa: S608
                (*fields.values(), user_id),
            )
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            raise
    return get_user(db, user_id)


def delete_user(db: sqlite3.Connection, user_id: int) -> bool:
    cursor = db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return cursor.rowcount > 0


def get_item(db: sqlite3.Connection, item_id: int) -> dict | None:
    row = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return row_to_dict(row) if row else None


def get_items(db: sqlite3.Connection, skip: int = 0, limit: int = 100) -> list[dict]:
    rows = db.execute(
        "SELECT * FROM items ORDER BY id LIMIT ? OFFSET ?",
        (limit, skip),
    ).fetchall()
    return [row_to_dict(row) for row in rows]


def create_item(db: sqlite3.Connection, data: ItemCreate) -> dict:
    try:
        cursor = db.execute(
            "INSERT INTO items (title, description, owner_id) VALUES (?, ?, ?)",
            (data.title, data.description, data.owner_id),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise
    item = get_item(db, _require_lastrowid(cursor))
    if item is None:
        raise RuntimeError("Failed to load item after insert")
    return item


def update_item(db: sqlite3.Connection, item_id: int, data: ItemUpdate) -> dict | None:
    if get_item(db, item_id) is None:
        return None
    fields = {
        key: value
        for key, value in data.model_dump(exclude_unset=True).items()
        if key in _ITEM_UPDATE_FIELDS
    }
    if fields:
        assignments = ", ".join(f"{column} = ?" for column in fields)
        db.execute(
            f"UPDATE items SET {assignments} WHERE id = ?",  # noqa: S608
            (*fields.values(), item_id),
        )
        db.commit()
    return get_item(db, item_id)


def delete_item(db: sqlite3.Connection, item_id: int) -> bool:
    cursor = db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    db.commit()
    return cursor.rowcount > 0
