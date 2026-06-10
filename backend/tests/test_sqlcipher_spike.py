"""
SQLCipher connectivity spike.

Proves the production encryption path (DatabaseManager) can create an
encrypted SQLite database, read data back with the correct key, and
rejects a wrong key.

The old version of this test built a `sqlite+pysqlcipher://` URL engine,
which SQLAlchemy 2.0 broke (it passes a `deterministic` kwarg that
pysqlcipher3 does not accept). DatabaseManager wraps connections to fix
exactly that, so the spike now exercises the same code path the app uses.

Run:
    pytest tests/test_sqlcipher_spike.py -v
"""

import os

import pytest
from sqlalchemy import text

from app.infrastructure.database import DatabaseManager, validate_hex_key

try:
    import pysqlcipher3.dbapi2  # noqa: F401
    _SQLCIPHER_AVAILABLE = True
except Exception:
    _SQLCIPHER_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _SQLCIPHER_AVAILABLE,
    reason="pysqlcipher3 / SQLCipher not available in this environment",
)

KEY = "a1b2c3d4e5f60718293a4b5c6d7e8f90"
WRONG_KEY = "00112233445566778899aabbccddeeff"


class TestSQLCipherSpike:
    """End-to-end proof that the DatabaseManager encryption path works."""

    def test_encrypted_db_works_with_correct_key(self, tmp_path):
        """Create an encrypted DB, write a row, read it back with a fresh engine."""
        db_file = str(tmp_path / "spike_correct.sqlite")

        manager = DatabaseManager(str(tmp_path))
        manager.initialize_encrypted(db_file, KEY)
        with manager.engine.connect() as conn:
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS spike (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
            ))
            conn.execute(text("INSERT INTO spike (name) VALUES ('ZeroWhisper')"))
            conn.commit()
        manager.dispose()

        assert os.path.exists(db_file), "Database file was not created."
        assert os.path.getsize(db_file) > 0, "Database file is empty."

        reader = DatabaseManager(str(tmp_path))
        reader.initialize_encrypted(db_file, KEY)
        with reader.engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM spike")).fetchall()
        reader.dispose()

        assert len(result) == 1, f"Expected 1 row, got {len(result)}."
        assert result[0][0] == "ZeroWhisper"

    def test_wrong_key_fails(self, tmp_path):
        """Opening the encrypted DB with a wrong key must raise."""
        db_file = str(tmp_path / "spike_wrong_key.sqlite")

        manager = DatabaseManager(str(tmp_path))
        manager.initialize_encrypted(db_file, KEY)
        with manager.engine.connect() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS canary (value TEXT)"))
            conn.execute(text("INSERT INTO canary (value) VALUES ('secret')"))
            conn.commit()
        manager.dispose()

        intruder = DatabaseManager(str(tmp_path))
        with pytest.raises(Exception):
            # initialize_encrypted runs create_all, which is the first read —
            # a wrong key fails here.
            intruder.initialize_encrypted(db_file, WRONG_KEY)
            with intruder.engine.connect() as conn:
                conn.execute(text("SELECT * FROM canary")).fetchall()
        intruder.dispose()

    def test_non_hex_key_rejected(self):
        """Keys must be hex — anything else is rejected before reaching PRAGMA."""
        with pytest.raises(ValueError):
            validate_hex_key("not-a-hex-key")
        with pytest.raises(ValueError):
            validate_hex_key("abc")  # odd length
        validate_hex_key(KEY)  # sanity: a real key passes
