"""
Database session management with SQLCipher encryption.

The encryption key is held only in memory — never persisted to disk.
The engine is recreated each time the key changes (first-run setup).
"""
from typing import Generator

from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine

class _PysqlcipherConnWrapper:
    """
    Thin proxy around a pysqlcipher3 connection that drops the `deterministic`
    kwarg from create_function — pysqlcipher3 doesn't accept it but
    SQLAlchemy 2.0 unconditionally passes it.
    """
    __slots__ = ("_conn",)

    def __init__(self, conn: object) -> None:
        self._conn = conn

    def create_function(self, name: str, narg: int, func: object, **_: object) -> None:
        self._conn.create_function(name, narg, func)  # type: ignore[attr-defined]

    def __getattr__(self, name: str) -> object:
        return getattr(self._conn, name)

# Module-level engine — replaced by initialize_engine() after first-run setup
_engine = None


def initialize_engine(db_path: str, key: str) -> None:
    """Create the SQLCipher-encrypted engine. Call this after the setup flow provides a key."""
    global _engine

    import pysqlcipher3.dbapi2 as _psc  # type: ignore[import-untyped]

    def _creator() -> _PysqlcipherConnWrapper:
        conn = _psc.connect(db_path, check_same_thread=False)
        conn.execute(f"PRAGMA key='{key}'")
        conn.execute("PRAGMA cipher='aes-256-cfb'")
        conn.execute("PRAGMA kdf_iter=64000")
        conn.execute("PRAGMA foreign_keys=ON")
        return _PysqlcipherConnWrapper(conn)

    # Use the plain sqlite dialect so SQLAlchemy doesn't inject its own
    # pysqlcipher on_connect handler (which double-sets PRAGMA key).
    # The creator already configures encryption and returns a compatible connection.
    _engine = create_engine("sqlite://", creator=_creator, echo=False)


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
