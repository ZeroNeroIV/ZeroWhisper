"""
First-run setup service.

State machine: UNINITIALIZED → INITIALIZED
State is stored in a small JSON file at settings.setup_state_path.
The encryption key is derived from the passphrase via PBKDF2 and held only in memory.
The salt used for derivation is stored in the state JSON so the key can be
re-derived on restart when the user provides their passphrase again.
"""
import hashlib
import json
import os
from enum import Enum
from pathlib import Path

from mnemonic import Mnemonic
from passlib.context import CryptContext

from app.config import settings
from app.database import initialize_engine, create_db_and_tables

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
mnemo = Mnemonic("english")

# In-memory key store — never written to disk
_current_key: str | None = None


class SetupState(str, Enum):
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZED = "INITIALIZED"


def _state_file() -> Path:
    path = Path(settings.setup_state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_state() -> SetupState:
    """Return the current setup state by reading the state JSON file."""
    f = _state_file()
    if not f.exists():
        return SetupState.UNINITIALIZED
    data = json.loads(f.read_text())
    return SetupState(data.get("state", "UNINITIALIZED"))


def _set_state(state: SetupState, extra: dict | None = None) -> None:
    """Write state (and optional extra fields) to the state JSON file."""
    existing: dict = {}
    f = _state_file()
    if f.exists():
        existing = json.loads(f.read_text())
    existing["state"] = state.value
    if extra:
        existing.update(extra)
    f.write_text(json.dumps(existing))


def _derive_key(passphrase: str, salt: bytes | None = None) -> tuple[str, bytes]:
    """Derive a 32-byte SQLCipher key from a passphrase using PBKDF2-SHA256."""
    if salt is None:
        salt = os.urandom(32)
    dk = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, iterations=260000)
    return dk.hex(), salt


def _key_to_mnemonic(key_hex: str) -> str:
    """Convert a hex key to a BIP39 mnemonic phrase."""
    key_bytes = bytes.fromhex(key_hex)
    return mnemo.to_mnemonic(key_bytes)


def _mnemonic_to_key(phrase: str) -> str:
    """Reconstruct key hex from BIP39 mnemonic."""
    if not mnemo.check(phrase):
        raise ValueError("Invalid BIP39 mnemonic phrase")
    seed = mnemo.to_entropy(phrase)
    return seed.hex()


def get_current_key() -> str | None:
    """Return the current in-memory encryption key, or None if not loaded."""
    return _current_key


def is_db_ready() -> bool:
    """Return True if the DB is INITIALIZED and the key is loaded in memory."""
    return get_state() == SetupState.INITIALIZED and _current_key is not None


def initialize_db(passphrase: str) -> str:
    """
    Initialize the encrypted database for the first time.

    Derives a 32-byte key from the passphrase via PBKDF2-SHA256, stores the
    salt in the state JSON (so the key can be re-derived on restart), creates
    the encrypted SQLite DB, runs table creation, and returns the BIP39 recovery
    phrase.

    The recovery phrase encodes the raw derived key bytes — it can reconstruct
    the key without needing the original passphrase or salt.

    Called only when state == UNINITIALIZED.
    """
    global _current_key

    if get_state() == SetupState.INITIALIZED:
        raise RuntimeError("Already initialized")

    key_hex, salt = _derive_key(passphrase)
    recovery_phrase = _key_to_mnemonic(key_hex)

    # Ensure the DB parent directory exists
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    initialize_engine(str(db_path), key_hex)
    create_db_and_tables()

    _current_key = key_hex
    _set_state(SetupState.INITIALIZED, extra={"salt_hex": salt.hex()})

    return recovery_phrase


def unlock_db(passphrase: str) -> bool:
    """
    Unlock an already-initialized DB using the passphrase.

    Re-derives the key using the stored salt, then opens the engine. Returns
    True on success, False if the passphrase is wrong or state is invalid.
    Called on each app restart before protected endpoints become available.
    """
    global _current_key

    state_file = _state_file()
    if not state_file.exists():
        return False

    data = json.loads(state_file.read_text())
    if data.get("state") != SetupState.INITIALIZED.value:
        return False

    salt_hex = data.get("salt_hex")
    if not salt_hex:
        return False

    salt = bytes.fromhex(salt_hex)
    key_hex, _ = _derive_key(passphrase, salt)

    try:
        initialize_engine(settings.db_path, key_hex)
        # Verify the key is correct by running a trivial query
        from sqlalchemy import text
        from app.database import get_engine
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        _current_key = key_hex
        return True
    except Exception:
        return False


def recover_db(recovery_phrase: str, new_passphrase: str) -> str:
    """
    Recover access using the BIP39 recovery phrase and set a new passphrase.

    Opens the DB with the key encoded in the recovery phrase, re-encrypts it
    with a key derived from new_passphrase (via SQLCipher PRAGMA rekey), stores
    the new salt, and returns the new BIP39 recovery phrase.

    Raises ValueError if the recovery phrase is invalid.
    """
    global _current_key

    old_key_hex = _mnemonic_to_key(recovery_phrase)  # raises ValueError if bad phrase
    new_key_hex, new_salt = _derive_key(new_passphrase)
    new_phrase = _key_to_mnemonic(new_key_hex)

    # Open DB with old key, then re-key it
    initialize_engine(settings.db_path, old_key_hex)
    from sqlalchemy import text
    from app.database import get_engine
    with get_engine().connect() as conn:
        conn.execute(text(f"PRAGMA rekey='{new_key_hex}'"))

    # Persist new salt and state
    _set_state(SetupState.INITIALIZED, extra={"salt_hex": new_salt.hex()})

    _current_key = new_key_hex
    return new_phrase
