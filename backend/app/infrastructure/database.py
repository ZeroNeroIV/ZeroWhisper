"""
Database engine management — class-based replacement for the module-level _engine.

The old database.py held _engine as a module global, making testing impossible
without monkeypatching. This class encapsulates engine lifecycle and accepts
configuration via the constructor.

PRAGMA keys are validated as hex before interpolation to prevent injection.
"""
from __future__ import annotations

from pathlib import Path
from sqlmodel import SQLModel, Session, create_engine
from typing import Generator
from app.core.config import settings


class _PysqlcipherConnWrapper:
    """Thin proxy around a pysqlcipher3 connection that drops the `deterministic`
    kwarg from create_function — pysqlcipher3 doesn't accept it but
    SQLAlchemy 2.0 unconditionally passes it."""
    __slots__ = ("_conn",)

    def __init__(self, conn: object) -> None:
        self._conn = conn

    def create_function(self, name: str, narg: int, func: object, **_: object) -> None:
        self._conn.create_function(name, narg, func)

    def __getattr__(self, name: str) -> object:
        return getattr(self._conn, name)


def validate_hex_key(key: str) -> None:
    """Validate that a key string is valid hex before using it in PRAGMA.

    This prevents SQL injection via f-string interpolation in PRAGMA key.
    """
    if not key or len(key) % 2 != 0:
        raise ValueError("Encryption key must be a valid hex string (even length)")
    try:
        int(key, 16)
    except ValueError:
        raise ValueError("Encryption key must be a valid hex string")


class DatabaseManager:
    """Manages SQLAlchemy engine lifecycle for encrypted and plain databases."""

    def __init__(self, db_dir: str) -> None:
        self._db_dir = Path(db_dir)
        self._db_dir.mkdir(parents=True, exist_ok=True)
        self._engine = None

    @staticmethod
    def _validate_hex_key(key: str) -> None:
        validate_hex_key(key)

    def _create_encrypted_engine(self, db_path: str, key: str) -> None:
        """Create a SQLCipher-encrypted engine with the given key.

        PRAGMA key is injected via the connection creator, never via URL.
        """
        self._validate_hex_key(key)
        import pysqlcipher3.dbapi2 as _psc

        def _creator() -> _PysqlcipherConnWrapper:
            conn = _psc.connect(db_path, check_same_thread=False)
            conn.execute(f"PRAGMA key='{key}'")
            conn.execute(f"PRAGMA cipher='{settings.cipher_algorithm}'")
            conn.execute(f"PRAGMA kdf_iter={settings.cipher_kdf_iter}")
            conn.execute("PRAGMA foreign_keys=ON")
            return _PysqlcipherConnWrapper(conn)

        self._engine = create_engine("sqlite://", creator=_creator, echo=False)

    def _create_plain_engine(self, db_path: str) -> None:
        """Create an unencrypted SQLite engine."""
        self._engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )

    def initialize_encrypted(self, db_path: str, key: str) -> None:
        """Initialize engine with SQLCipher encryption."""
        self._create_encrypted_engine(db_path, key)
        self._create_tables()

    def initialize_plain(self, db_path: str) -> None:
        """Initialize engine without encryption."""
        self._create_plain_engine(db_path)
        self._create_tables()

    def rekey(self, new_key: str) -> None:
        """Change the encryption key of the currently active database."""
        if self._engine is None:
            raise RuntimeError("No active database engine")
        self._validate_hex_key(new_key)
        from sqlalchemy import text
        with self._engine.connect() as conn:
            conn.execute(text(f"PRAGMA rekey='{new_key}'"))
            conn.commit()

    def _create_tables(self) -> None:
        """Create all tables defined in SQLModel metadata."""
        if self._engine is None:
            raise RuntimeError("Engine not initialized")
        SQLModel.metadata.create_all(self._engine)
        self._run_migrations()

    def _run_migrations(self) -> None:
        """Run manual ALTER TABLE migrations for columns added after initial creation.

        SQLCipher + Alembic has compatibility issues, so we do incremental
        ALTER TABLE here. New columns must be added as nullable or with defaults.
        """
        from sqlalchemy import text, inspect
        if self._engine is None:
            return
        with self._engine.connect() as conn:
            # Check which tables already exist
            inspector = inspect(conn)
            existing = inspector.get_table_names()

            # Category icon column
            if "category" in existing:
                try:
                    col_names = [c["name"] for c in inspector.get_columns("category")]
                    if "icon" not in col_names:
                        conn.execute(text("ALTER TABLE category ADD COLUMN icon VARCHAR"))
                        conn.commit()
                except Exception:
                    conn.rollback()

            # Wallet + wallet_id on transaction (added in wallet feature)
            if "transaction" in existing:
                try:
                    col_names = [c["name"] for c in inspector.get_columns("transaction")]
                    if "wallet_id" not in col_names:
                        conn.execute(text("ALTER TABLE transaction ADD COLUMN wallet_id VARCHAR"))
                        conn.commit()
                except Exception:
                    conn.rollback()

    @property
    def engine(self):
        """Public read-only access to the underlying SQLAlchemy engine."""
        return self._engine

    def get_session(self) -> Generator[Session, None, None]:
        """FastAPI-compatible session generator."""
        if self._engine is None:
            raise RuntimeError("Database engine not initialized")
        with Session(self._engine) as session:
            yield session

    def is_ready(self) -> bool:
        return self._engine is not None

    def dispose(self) -> None:
        if self._engine:
            self._engine.dispose()
            self._engine = None
