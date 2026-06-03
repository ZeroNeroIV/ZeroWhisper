"""
ApiKeyRepository port — abstract persistence contract for API keys.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.core.domain.user import User


class ApiKeyData:
    """Read-only API key data returned by the repository."""
    def __init__(self, id: int, prefix: str, name: str, last_used_at: datetime | None, created_at: datetime, user_id: UUID) -> None:
        self.id = id
        self.prefix = prefix
        self.name = name
        self.last_used_at = last_used_at
        self.created_at = created_at
        self.user_id = user_id


class ApiKeyRepository(ABC):

    @abstractmethod
    def create(self, user_id: UUID, key_hash: str, prefix: str, name: str) -> ApiKeyData:
        ...

    @abstractmethod
    def list_by_user(self, user_id: UUID) -> list[ApiKeyData]:
        ...

    @abstractmethod
    def revoke(self, key_id: int, user_id: UUID) -> bool:
        ...

    @abstractmethod
    def find_user_by_key_hash(self, key_hash: str) -> tuple[User, int] | None:
        """Return (User, key_id) if valid active key exists, else None."""

    @abstractmethod
    def touch_last_used(self, key_id: int) -> None:
        ...
