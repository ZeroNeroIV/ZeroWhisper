"""
Multi-vault setup service.

Each vault is an independent SQLCipher-encrypted database.  Only one vault is
active (unlocked) at a time; the encryption key is held only in memory.
Vault metadata (name, db_path, derivation salt) is persisted to a JSON file.

State file format:
  {
    "vaults": {
      "<uuid>": {
        "name": "Personal",
        "db_path": "data/vault-<uuid>.db",
        "salt_hex": "<hex>",
        "created_at": "<iso8601>"
      },
      ...
    }
  }

Migration: if the file contains the old single-vault format
  {"state": "INITIALIZED", "salt_hex": "..."}
it is automatically converted on first read.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from uuid import uuid4

from mnemonic import Mnemonic

from app.config import settings
from app.database import initialize_engine, initialize_plain_engine, create_db_and_tables

mnemo = Mnemonic("english")

VAULT_TYPE_SECURE = "secure"
VAULT_TYPE_OPEN = "open"

# In-memory state — never written to disk
_active_vault_id: str | None = None
_current_key: str | None = None
_db_ready: bool = False


class SetupState(str, Enum):
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZED = "INITIALIZED"


# ── State file helpers ──────────────────────────────────────────────────────────

def _state_file() -> Path:
    path = Path(settings.setup_state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_state() -> dict:
    """Load state JSON, migrating old single-vault format if present."""
    f = _state_file()
    if not f.exists():
        return {"vaults": {}}
    data = json.loads(f.read_text())
    # Migrate old format: {state, salt_hex} → {vaults: {...}}
    if "salt_hex" in data and "vaults" not in data:
        vault_id = str(uuid4())
        migrated: dict = {
            "vaults": {
                vault_id: {
                    "name": "Default",
                    "db_path": settings.db_path,
                    "salt_hex": data["salt_hex"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            }
        }
        f.write_text(json.dumps(migrated, indent=2))
        return migrated
    return data


def _save_state(data: dict) -> None:
    _state_file().write_text(json.dumps(data, indent=2))


# ── Crypto helpers ──────────────────────────────────────────────────────────────

def _derive_key(passphrase: str, salt: bytes | None = None) -> tuple[str, bytes]:
    if salt is None:
        salt = os.urandom(32)
    dk = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, iterations=260000)
    return dk.hex(), salt


def _key_to_mnemonic(key_hex: str) -> str:
    return mnemo.to_mnemonic(bytes.fromhex(key_hex))


def _mnemonic_to_key(phrase: str) -> str:
    if not mnemo.check(phrase):
        raise ValueError("Invalid BIP39 mnemonic phrase")
    return mnemo.to_entropy(phrase).hex()


def _verify_key(db_path: str, key_hex: str) -> bool:
    """
    Open a raw pysqlcipher3 connection and read sqlite_master to confirm
    the key decrypts page 1 correctly.  Never modifies global engine state.
    """
    import pysqlcipher3.dbapi2 as _psc  # type: ignore[import-untyped]
    try:
        conn = _psc.connect(db_path, check_same_thread=False)
        conn.execute(f"PRAGMA key='{key_hex}'")
        conn.execute("PRAGMA cipher='aes-256-cfb'")
        conn.execute("PRAGMA kdf_iter=64000")
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        conn.close()
        return True
    except Exception:
        return False


# ── Public read API ─────────────────────────────────────────────────────────────

def get_state() -> SetupState:
    """UNINITIALIZED if no vaults exist on disk, INITIALIZED otherwise."""
    state = _load_state()
    return SetupState.INITIALIZED if state.get("vaults") else SetupState.UNINITIALIZED


def is_db_ready() -> bool:
    """True when a vault is unlocked and the engine is ready."""
    return _active_vault_id is not None and _db_ready


def get_current_key() -> str | None:
    return _current_key


def get_active_vault_id() -> str | None:
    return _active_vault_id


def get_vault(vault_id: str) -> dict | None:
    """Return vault metadata dict or None if not found."""
    return _load_state().get("vaults", {}).get(vault_id)


def list_vaults() -> list[dict]:
    """Return all vaults sorted by creation date, with is_active flag."""
    vaults = _load_state().get("vaults", {})
    result = [
        {
            "id": vid,
            "name": meta["name"],
            "vault_type": meta.get("vault_type", VAULT_TYPE_SECURE),
            "created_at": meta.get("created_at"),
            "is_active": vid == _active_vault_id,
        }
        for vid, meta in vaults.items()
    ]
    result.sort(key=lambda v: v.get("created_at") or "")
    return result


def verify_passphrase(passphrase: str) -> bool:
    """Re-derive the key for the active vault and compare with in-memory key."""
    if _current_key is None or _active_vault_id is None:
        return False
    vault = get_vault(_active_vault_id)
    if not vault:
        return False
    salt = bytes.fromhex(vault["salt_hex"])
    derived, _ = _derive_key(passphrase, salt)
    return derived == _current_key


# ── Vault management ────────────────────────────────────────────────────────────

def create_vault(name: str, passphrase: str) -> tuple[str, str]:
    """
    Create a new encrypted vault, activate it immediately, and return
    (vault_id, recovery_phrase).
    """
    global _active_vault_id, _current_key

    vault_id = str(uuid4())
    key_hex, salt = _derive_key(passphrase)
    recovery_phrase = _key_to_mnemonic(key_hex)

    state = _load_state()
    is_first = not state.get("vaults")

    # First vault keeps the configured db_path for backward compat.
    # Additional vaults get UUID-scoped filenames.
    if is_first:
        db_path = Path(settings.db_path)
    else:
        db_path = Path(settings.db_path).parent / f"vault-{vault_id}.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    initialize_engine(str(db_path), key_hex)
    create_db_and_tables()

    state.setdefault("vaults", {})[vault_id] = {
        "name": name,
        "db_path": str(db_path),
        "vault_type": VAULT_TYPE_SECURE,
        "salt_hex": salt.hex(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_state(state)

    _active_vault_id = vault_id
    _current_key = key_hex
    _db_ready = True
    return vault_id, recovery_phrase


def create_open_vault(name: str) -> str:
    """
    Create a new unencrypted open vault, activate it immediately, and return vault_id.
    Open vaults require no passphrase and auto-unlock on server startup.
    """
    global _active_vault_id, _current_key, _db_ready

    vault_id = str(uuid4())
    state = _load_state()
    is_first = not state.get("vaults")

    if is_first:
        db_path = Path(settings.db_path)
    else:
        db_path = Path(settings.db_path).parent / f"vault-{vault_id}.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    initialize_plain_engine(str(db_path))
    create_db_and_tables()

    state.setdefault("vaults", {})[vault_id] = {
        "name": name,
        "db_path": str(db_path),
        "vault_type": VAULT_TYPE_OPEN,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_state(state)

    _active_vault_id = vault_id
    _current_key = None
    _db_ready = True
    return vault_id


def unlock_vault(vault_id: str, passphrase: str) -> bool:
    """
    Unlock a specific vault and make it active.
    Returns False if the vault does not exist or the passphrase is wrong.
    """
    global _active_vault_id, _current_key

    vault = get_vault(vault_id)
    if not vault:
        return False

    salt = bytes.fromhex(vault["salt_hex"])
    key_hex, _ = _derive_key(passphrase, salt)

    if not _verify_key(vault["db_path"], key_hex):
        return False

    initialize_engine(vault["db_path"], key_hex)
    _active_vault_id = vault_id
    _current_key = key_hex
    _db_ready = True
    return True


def unlock_open_vault(vault_id: str) -> bool:
    """Unlock an open vault without passphrase. Returns False if vault not found or not open type."""
    global _active_vault_id, _current_key, _db_ready

    vault = get_vault(vault_id)
    if not vault or vault.get("vault_type") != VAULT_TYPE_OPEN:
        return False

    initialize_plain_engine(vault["db_path"])
    _active_vault_id = vault_id
    _current_key = None
    _db_ready = True
    return True


def auto_unlock_open_vaults() -> bool:
    """
    Auto-unlock the first open vault found. Called at server startup.
    Returns True if a vault was unlocked (or one was already active).
    """
    if _db_ready:
        return True
    vaults = _load_state().get("vaults", {})
    for vid, meta in vaults.items():
        if meta.get("vault_type") == VAULT_TYPE_OPEN:
            return unlock_open_vault(vid)
    return False


def recover_vault(vault_id: str, recovery_phrase: str, new_passphrase: str) -> str:
    """
    Recover a vault using its BIP39 recovery phrase, re-key it with
    new_passphrase, and return the new recovery phrase.
    Raises ValueError if the recovery phrase is invalid.
    """
    global _active_vault_id, _current_key

    vault = get_vault(vault_id)
    if not vault:
        raise ValueError("Vault not found")

    old_key_hex = _mnemonic_to_key(recovery_phrase)
    new_key_hex, new_salt = _derive_key(new_passphrase)
    new_phrase = _key_to_mnemonic(new_key_hex)

    initialize_engine(vault["db_path"], old_key_hex)
    from sqlalchemy import text
    from app.database import get_engine
    with get_engine().connect() as conn:
        conn.execute(text(f"PRAGMA rekey='{new_key_hex}'"))

    state = _load_state()
    state["vaults"][vault_id]["salt_hex"] = new_salt.hex()
    _save_state(state)

    _active_vault_id = vault_id
    _current_key = new_key_hex
    _db_ready = True
    return new_phrase


# ── Backward-compat wrappers (used by existing /setup/* endpoints) ──────────────

def initialize_db(passphrase: str) -> str:
    """First-time initialization — creates 'Default' vault. Returns recovery phrase."""
    if get_state() == SetupState.INITIALIZED:
        raise RuntimeError("Already initialized")
    _, recovery_phrase = create_vault("Default", passphrase)
    return recovery_phrase


def unlock_db(passphrase: str) -> bool:
    """Unlock the first registered vault (backward-compat)."""
    vaults = _load_state().get("vaults", {})
    if not vaults:
        return False
    first_id = next(iter(vaults))
    return unlock_vault(first_id, passphrase)


def recover_db(recovery_phrase: str, new_passphrase: str) -> str:
    """Recover the first registered vault (backward-compat)."""
    vaults = _load_state().get("vaults", {})
    if not vaults:
        raise ValueError("No vaults found")
    first_id = next(iter(vaults))
    return recover_vault(first_id, recovery_phrase, new_passphrase)
