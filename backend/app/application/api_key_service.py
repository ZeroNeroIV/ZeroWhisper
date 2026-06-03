"""
API key management use case — generate, list, revoke, verify keys.
"""
from __future__ import annotations

import hashlib
import secrets
from uuid import UUID

from app.core.domain.user import User
from app.core.ports.api_key_repo import ApiKeyData, ApiKeyRepository

KEY_PREFIX = "zwp_"
KEY_BYTES = 32


class ApiKeyService:

    def __init__(self, repo: ApiKeyRepository) -> None:
        self._repo = repo

    @staticmethod
    def _generate_raw_key() -> str:
        return KEY_PREFIX + secrets.token_urlsafe(KEY_BYTES)

    @staticmethod
    def _hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def create(self, user_id: UUID, name: str) -> tuple[ApiKeyData, str]:
        raw_key = self._generate_raw_key()
        key_hash = self._hash_key(raw_key)
        data = self._repo.create(user_id, key_hash, raw_key[:12], name)
        return data, raw_key

    def list_keys(self, user_id: UUID) -> list[ApiKeyData]:
        return self._repo.list_by_user(user_id)

    def revoke(self, key_id: int, user_id: UUID) -> bool:
        return self._repo.revoke(key_id, user_id)

    def verify(self, raw_key: str) -> User | None:
        """Validate a raw API key. Returns the owning User or None. Touches last_used_at."""
        key_hash = self._hash_key(raw_key)
        result = self._repo.find_user_by_key_hash(key_hash)
        if result is None:
            return None
        user, key_id = result
        self._repo.touch_last_used(key_id)
        return user
