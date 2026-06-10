"""
SqlCipherVaultManager — concrete VaultManager implementation.

Replaces the module-level state in app/services/setup.py with a proper class
that manages vault lifecycle through the DatabaseManager.

Key improvements over the old setup.py:
1. No module-level globals — all state is instance-attached
2. DatabaseManager handles engine lifecycle, not this class
3. PRAGMA keys are validated as hex before interpolation
4. All crypto parameters come from Config, not hardcoded
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from mnemonic import Mnemonic

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.core.ports.vault_manager import VaultManager
from app.infrastructure.database import DatabaseManager, validate_hex_key

mnemo = Mnemonic("english")

VAULT_TYPE_SECURE = "secure"
VAULT_TYPE_OPEN = "open"


class SqlCipherVaultManager(VaultManager):

    def __init__(self, db_manager: DatabaseManager, state_path: str) -> None:
        self._db = db_manager
        self._state_path = Path(state_path)
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._active_vault_id: str | None = None
        self._current_key: str | None = None
        self._db_ready: bool = False

    # ── State persistence ─────────────────────────────────────────────────────────

    def _load_state(self) -> dict:
        if not self._state_path.exists():
            return {"vaults": {}}
        data = json.loads(self._state_path.read_text())
        if "salt_hex" in data and "vaults" not in data:
            return self._migrate_old_format(data)
        return data

    def _save_state(self, data: dict) -> None:
        self._state_path.write_text(json.dumps(data, indent=2))

    def _migrate_old_format(self, old: dict) -> dict:
        vault_id = str(uuid4())
        migrated = {
            "vaults": {
                vault_id: {
                    "name": "Default",
                    "db_path": old.get("db_path", settings.db_path),
                    "salt_hex": old["salt_hex"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            }
        }
        self._save_state(migrated)
        return migrated

    # ── Crypto ────────────────────────────────────────────────────────────────────

    @staticmethod
    def _derive_key(passphrase: str, salt: bytes | None = None) -> tuple[str, bytes]:
        if salt is None:
            salt = SqlCipherVaultManager._create_salt()
        dk = hashlib.pbkdf2_hmac(
            settings.pbkdf2_hash,
            passphrase.encode("utf-8"),
            salt,
            iterations=settings.pbkdf2_iterations,
        )
        return dk.hex(), salt

    @staticmethod
    def _create_salt() -> bytes:
        """Generate a random 32-byte salt for key derivation.

        Must match the old setup.py behavior for cross-compatibility.
        """
        import os
        return os.urandom(32)

    @staticmethod
    def _key_to_mnemonic(key_hex: str) -> str:
        return mnemo.to_mnemonic(bytes.fromhex(key_hex))

    @staticmethod
    def _mnemonic_to_key(phrase: str) -> str:
        if not mnemo.check(phrase):
            raise ValidationError("Invalid BIP39 mnemonic phrase")
        return mnemo.to_entropy(phrase).hex()

    @staticmethod
    def _verify_key(db_path: str, key_hex: str) -> bool:
        import pysqlcipher3.dbapi2 as _psc
        try:
            validate_hex_key(key_hex)
            conn = _psc.connect(db_path, check_same_thread=False)
            conn.execute(f"PRAGMA key='{key_hex}'")
            conn.execute(f"PRAGMA cipher='{settings.cipher_algorithm}'")
            conn.execute(f"PRAGMA kdf_iter={settings.cipher_kdf_iter}")
            conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
            conn.close()
            return True
        except Exception:
            return False

    # ── VaultManager interface ────────────────────────────────────────────────────

    def is_db_ready(self) -> bool:
        return self._active_vault_id is not None and self._db_ready

    def get_state(self) -> str:
        state = self._load_state()
        return "INITIALIZED" if state.get("vaults") else "UNINITIALIZED"

    def get_active_vault_id(self) -> str | None:
        return self._active_vault_id

    def list_vaults(self) -> list[dict]:
        vaults = self._load_state().get("vaults", {})
        result = [
            {
                "id": vid,
                "name": meta["name"],
                "vault_type": meta.get("vault_type", VAULT_TYPE_SECURE),
                "created_at": meta.get("created_at"),
                "is_active": vid == self._active_vault_id,
            }
            for vid, meta in vaults.items()
        ]
        result.sort(key=lambda v: v.get("created_at") or "")
        return result

    def create_vault(self, name: str, passphrase: str) -> tuple[str, str]:
        vault_id = str(uuid4())
        key_hex, salt = self._derive_key(passphrase)
        recovery_phrase = self._key_to_mnemonic(key_hex)

        state = self._load_state()
        is_first = not state.get("vaults")
        db_path = settings.db_path if is_first else settings.vault_db_path(vault_id)

        self._db.initialize_encrypted(db_path, key_hex)

        state.setdefault("vaults", {})[vault_id] = {
            "name": name,
            "db_path": db_path,
            "vault_type": VAULT_TYPE_SECURE,
            "salt_hex": salt.hex(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_state(state)

        self._active_vault_id = vault_id
        self._current_key = key_hex
        self._db_ready = True
        return vault_id, recovery_phrase

    def create_open_vault(self, name: str) -> str:
        vault_id = str(uuid4())
        state = self._load_state()
        is_first = not state.get("vaults")
        db_path = settings.db_path if is_first else settings.vault_db_path(vault_id)

        self._db.initialize_plain(db_path)

        state.setdefault("vaults", {})[vault_id] = {
            "name": name,
            "db_path": db_path,
            "vault_type": VAULT_TYPE_OPEN,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_state(state)

        self._active_vault_id = vault_id
        self._current_key = None
        self._db_ready = True
        return vault_id

    def unlock_vault(self, vault_id: str, passphrase: str) -> bool:
        state = self._load_state()
        vault = state.get("vaults", {}).get(vault_id)
        if not vault:
            return False

        salt = bytes.fromhex(vault["salt_hex"])
        key_hex, _ = self._derive_key(passphrase, salt)

        if not self._verify_key(vault["db_path"], key_hex):
            return False

        self._db.initialize_encrypted(vault["db_path"], key_hex)
        self._active_vault_id = vault_id
        self._current_key = key_hex
        self._db_ready = True
        return True

    def unlock_open_vault(self, vault_id: str) -> bool:
        state = self._load_state()
        vault = state.get("vaults", {}).get(vault_id)
        if not vault or vault.get("vault_type") != VAULT_TYPE_OPEN:
            return False

        self._db.initialize_plain(vault["db_path"])
        self._active_vault_id = vault_id
        self._current_key = None
        self._db_ready = True
        return True

    def recover_vault(self, vault_id: str, recovery_phrase: str, new_passphrase: str) -> str:
        state = self._load_state()
        vault = state.get("vaults", {}).get(vault_id)
        if not vault:
            raise ValidationError("Vault not found")

        old_key_hex = self._mnemonic_to_key(recovery_phrase)
        new_key_hex, new_salt = self._derive_key(new_passphrase)
        new_phrase = self._key_to_mnemonic(new_key_hex)

        self._db.initialize_encrypted(vault["db_path"], old_key_hex)
        self._db.rekey(new_key_hex)

        state["vaults"][vault_id]["salt_hex"] = new_salt.hex()
        self._save_state(state)

        self._active_vault_id = vault_id
        self._current_key = new_key_hex
        self._db_ready = True
        return new_phrase

    def verify_passphrase(self, passphrase: str) -> bool:
        if self._current_key is None or self._active_vault_id is None:
            return False
        state = self._load_state()
        vault = state.get("vaults", {}).get(self._active_vault_id)
        if not vault:
            return False
        salt = bytes.fromhex(vault["salt_hex"])
        derived, _ = self._derive_key(passphrase, salt)
        return derived == self._current_key

    def auto_unlock_open_vaults(self) -> bool:
        if self._db_ready:
            return True
        state = self._load_state()
        for vid, meta in state.get("vaults", {}).items():
            if meta.get("vault_type") == VAULT_TYPE_OPEN:
                return self.unlock_open_vault(vid)
        return False

    # ── Backward-compat wrappers (used by old /setup/* endpoints) ──────────────

    def initialize(self, passphrase: str) -> str:
        """Backward-compat: create 'Default' vault. Returns recovery phrase."""
        _, phrase = self.create_vault("Default", passphrase)
        return phrase

    def unlock(self, passphrase: str) -> bool:
        """Backward-compat: unlock the first vault."""
        state = self._load_state()
        vaults = state.get("vaults", {})
        if not vaults:
            return False
        first_id = next(iter(vaults))
        return self.unlock_vault(first_id, passphrase)

    def recover(self, recovery_phrase: str, new_passphrase: str) -> str:
        """Backward-compat: recover the first vault."""
        state = self._load_state()
        vaults = state.get("vaults", {})
        if not vaults:
            raise ValidationError("No vaults found")
        first_id = next(iter(vaults))
        return self.recover_vault(first_id, recovery_phrase, new_passphrase)

    def get_vault(self, vault_id: str) -> dict | None:
        """Return vault metadata dict or None if not found."""
        return self._load_state().get("vaults", {}).get(vault_id)
