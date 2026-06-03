"""
VaultManager port — abstract contract for vault lifecycle.

The vault subsystem manages encrypted (SQLCipher) and unencrypted SQLite
database instances. Only one vault is active at a time; its encryption key
is held in memory and never persisted.

Why an interface?
- The old setup.py mixed crypto, file I/O, state management, and engine init
- Testing required monkeypatching module-level globals
- Vault management should be swappable (e.g. for tests that always use a temp file)
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class VaultManager(ABC):
    """Manages the lifecycle of encrypted and unencrypted vaults."""

    @abstractmethod
    def is_db_ready(self) -> bool:
        """True when a vault is unlocked and queries can execute."""
        ...

    @abstractmethod
    def get_state(self) -> str:
        """'UNINITIALIZED' if no vaults exist, 'INITIALIZED' otherwise."""
        ...

    @abstractmethod
    def create_vault(self, name: str, passphrase: str) -> tuple[str, str]:
        """Create a new encrypted vault, activate it, return (vault_id, recovery_phrase)."""
        ...

    @abstractmethod
    def create_open_vault(self, name: str) -> str:
        """Create a new unencrypted open vault, activate it, return vault_id."""
        ...

    @abstractmethod
    def unlock_vault(self, vault_id: str, passphrase: str) -> bool:
        """Unlock a secure vault. Returns False if passphrase is wrong."""
        ...

    @abstractmethod
    def unlock_open_vault(self, vault_id: str) -> bool:
        """Unlock an open vault (no passphrase needed)."""
        ...

    @abstractmethod
    def recover_vault(self, vault_id: str, recovery_phrase: str, new_passphrase: str) -> str:
        """Recover using BIP39 phrase, re-key, return new recovery phrase."""
        ...

    @abstractmethod
    def verify_passphrase(self, passphrase: str) -> bool:
        """Check passphrase against the currently active vault."""
        ...

    @abstractmethod
    def list_vaults(self) -> list[dict]:
        """Return all vaults with metadata and active status."""
        ...

    @abstractmethod
    def get_active_vault_id(self) -> str | None:
        ...

    @abstractmethod
    def auto_unlock_open_vaults(self) -> bool:
        """Called at startup to auto-unlock any open vaults."""
        ...
