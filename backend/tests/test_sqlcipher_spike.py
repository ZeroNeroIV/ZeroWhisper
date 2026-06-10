"""
SQLCipher connectivity spike — Task 1.

Proves that pysqlcipher3 can create an encrypted SQLite database, read data
back with the correct key, and correctly rejects a wrong key.

Run as a pytest suite:
    pytest tests/test_sqlcipher_spike.py -v

Run as a standalone script from backend/:
    python tests/test_sqlcipher_spike.py
"""

import os
import tempfile
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DatabaseError, OperationalError


def _cipher_url(db_path: str, key: str) -> str:
    """Build a pysqlcipher3 SQLAlchemy connection URL.

    URL form:
        sqlite+pysqlcipher://:KEY@/ABSOLUTE_PATH?cipher=aes-256-cfb&kdf_iter=64000

    The key goes in the password slot; the host is empty; the path is
    absolute (leading slash is part of the netloc→path transition).
    """
    # Ensure we use an absolute path so the URL is unambiguous.
    abs_path = os.path.abspath(db_path)
    return (
        f"sqlite+pysqlcipher://:{key}@/{abs_path}"
        "?cipher=aes-256-cfb&kdf_iter=64000"
    )


class TestSQLCipherSpike:
    """End-to-end proof that pysqlcipher3 encryption works correctly."""

    def test_encrypted_db_works_with_correct_key(self, tmp_path):
        """Create an encrypted DB, write a row, read it back."""
        db_file = str(tmp_path / "spike_correct.sqlite")
        key = "super-secret-passphrase-for-test"

        # --- Write phase ---
        engine_write = create_engine(_cipher_url(db_file, key), echo=False)
        with engine_write.connect() as conn:
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS spike ("
                "  id   INTEGER PRIMARY KEY,"
                "  name TEXT NOT NULL"
                ")"
            ))
            conn.execute(text("INSERT INTO spike (name) VALUES ('ZeroWhisper')"))
            conn.commit()
        engine_write.dispose()

        # Verify the on-disk file exists and is non-empty.
        assert os.path.exists(db_file), "Database file was not created."
        assert os.path.getsize(db_file) > 0, "Database file is empty."

        # --- Read phase (fresh engine, same key) ---
        engine_read = create_engine(_cipher_url(db_file, key), echo=False)
        with engine_read.connect() as conn:
            result = conn.execute(text("SELECT name FROM spike")).fetchall()
        engine_read.dispose()

        assert len(result) == 1, f"Expected 1 row, got {len(result)}."
        assert result[0][0] == "ZeroWhisper", (
            f"Unexpected value: {result[0][0]!r}"
        )

    def test_wrong_key_fails(self, tmp_path):
        """Opening the encrypted DB with a wrong key must raise an exception."""
        db_file = str(tmp_path / "spike_wrong_key.sqlite")
        correct_key = "the-correct-passphrase"
        wrong_key = "totally-wrong-passphrase"

        # Create and populate the database with the correct key.
        engine_create = create_engine(_cipher_url(db_file, correct_key), echo=False)
        with engine_create.connect() as conn:
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS canary ("
                "  value TEXT"
                ")"
            ))
            conn.execute(text("INSERT INTO canary (value) VALUES ('secret')"))
            conn.commit()
        engine_create.dispose()

        # Attempt to open it with the wrong key — must fail.
        engine_wrong = create_engine(_cipher_url(db_file, wrong_key), echo=False)
        raised = False
        try:
            with engine_wrong.connect() as conn:
                # pysqlcipher3 raises on the first query when the key is wrong.
                conn.execute(text("SELECT * FROM canary")).fetchall()
        except (DatabaseError, OperationalError, Exception):
            raised = True
        finally:
            engine_wrong.dispose()

        assert raised, (
            "Expected an exception when opening the database with the wrong key, "
            "but none was raised. The database may not be encrypted."
        )


# ---------------------------------------------------------------------------
# Standalone entry-point
# ---------------------------------------------------------------------------

def _run_standalone():
    """Run both tests without pytest and print a human-readable report."""
    import traceback

    passed = 0
    failed = 0

    with tempfile.TemporaryDirectory() as tmpdir:

        class FakeTmpPath:
            """Minimal stand-in for pytest's tmp_path fixture."""
            def __init__(self, base):
                self._base = base

            def __truediv__(self, name):
                return type("P", (), {
                    "__str__": lambda s: os.path.join(self._base, name)
                })()

        tmp = FakeTmpPath(tmpdir)
        suite = TestSQLCipherSpike()

        tests = [
            ("test_encrypted_db_works_with_correct_key",
             lambda: suite.test_encrypted_db_works_with_correct_key(tmp)),
            ("test_wrong_key_fails",
             lambda: suite.test_wrong_key_fails(tmp)),
        ]

        for name, fn in tests:
            print(f"  Running {name} ... ", end="", flush=True)
            try:
                fn()
                print("PASSED")
                passed += 1
            except Exception:
                print("FAILED")
                traceback.print_exc()
                failed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed.")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    print("SQLCipher spike — standalone run")
    print("=" * 40)
    _run_standalone()
