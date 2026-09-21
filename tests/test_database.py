import pytest

from database import sqlite_path


def test_sqlite_memory_urls():
    assert sqlite_path("sqlite:///:memory:") == ":memory:"
    assert sqlite_path(":memory:") == ":memory:"


def test_sqlite_relative_and_absolute_urls():
    assert sqlite_path("sqlite:///./app.db") == "./app.db"
    assert sqlite_path("sqlite:////app/data/app.db") == "/app/data/app.db"
    assert sqlite_path("./app.db") == "./app.db"


def test_sqlite_file_uri_passthrough():
    uri = "file:testdb?mode=memory&cache=shared"
    assert sqlite_path(uri) == uri


def test_rejects_non_sqlite_urls():
    with pytest.raises(RuntimeError, match="sqlite3 stdlib"):
        sqlite_path("postgresql+psycopg://localhost/db")
