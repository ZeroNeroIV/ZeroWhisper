"""
Database session management — delegates to shared DatabaseManager.

Old code still uses this module's get_session(), initialize_engine(), etc.
They all delegate to a module-level DatabaseManager instance that is the
SAME object used by the Container — so engine state stays in sync.
"""
from typing import Generator

from sqlmodel import Session

from app.infrastructure.database import DatabaseManager

_db_manager = DatabaseManager("data")


def initialize_engine(db_path: str, key: str) -> None:
    _db_manager.initialize_encrypted(db_path, key)


def initialize_plain_engine(db_path: str) -> None:
    _db_manager.initialize_plain(db_path)


def get_session() -> Generator[Session, None, None]:
    return _db_manager.get_session()
