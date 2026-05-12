"""
Database session management with SQLCipher encryption.

The encryption key is held only in memory — never persisted to disk.
The engine is recreated each time the key changes (first-run setup).
"""
from typing import Generator

from sqlalchemy import event, text
from sqlmodel import SQLModel, Session, create_engine

# Module-level engine — replaced by initialize_engine() after first-run setup
_engine = None


def initialize_engine(db_path: str, key: str) -> None:
    """Create the SQLCipher-encrypted engine. Call this after the setup flow provides a key."""
    global _engine
    url = f"sqlite+pysqlcipher://:{key}@/{db_path}?cipher=aes-256-cfb&kdf_iter=64000"
    _engine = create_engine(url, echo=False)

    @event.listens_for(_engine, "connect")
    def _set_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute(f"PRAGMA key='{key}'")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_engine():
    if _engine is None:
        raise RuntimeError("Database not initialized. Complete first-run setup first.")
    return _engine


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(get_engine())


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    with Session(get_engine()) as session:
        yield session
