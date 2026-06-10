"""
SQLModel-backed ApiKeyRepository implementation.
"""
from __future__ import annotations

from app.core.time import utc_now
from uuid import UUID

from sqlmodel import Session, select

from app.core.domain.user import User
from app.core.ports.api_key_repo import ApiKeyData, ApiKeyRepository
from app.models.api_key import ApiKey as ORMApiKey
from app.models.user import User as ORMUser


class SQLModelApiKeyRepository(ApiKeyRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, user_id: UUID, key_hash: str, prefix: str, name: str) -> ApiKeyData:
        orm = ORMApiKey(user_id=user_id, key_hash=key_hash, prefix=prefix, name=name)
        self._session.add(orm)
        self._session.flush()
        self._session.refresh(orm)
        return ApiKeyData(
            id=orm.id, prefix=orm.prefix, name=orm.name,
            last_used_at=orm.last_used_at, created_at=orm.created_at,
            user_id=orm.user_id,
        )

    def list_by_user(self, user_id: UUID) -> list[ApiKeyData]:
        rows = self._session.exec(
            select(ORMApiKey).where(ORMApiKey.user_id == user_id, ORMApiKey.is_active == True)
        ).all()
        return [
            ApiKeyData(
                id=r.id, prefix=r.prefix, name=r.name,
                last_used_at=r.last_used_at, created_at=r.created_at,
                user_id=r.user_id,
            )
            for r in rows
        ]

    def revoke(self, key_id: int, user_id: UUID) -> bool:
        key = self._session.exec(
            select(ORMApiKey).where(ORMApiKey.id == key_id, ORMApiKey.user_id == user_id)
        ).first()
        if not key:
            return False
        key.is_active = False
        self._session.add(key)
        self._session.flush()
        return True

    def find_user_by_key_hash(self, key_hash: str) -> tuple[User, int] | None:
        api_key = self._session.exec(
            select(ORMApiKey).where(ORMApiKey.key_hash == key_hash, ORMApiKey.is_active == True)
        ).first()
        if not api_key:
            return None
        orm = self._session.get(ORMUser, str(api_key.user_id))
        if not orm:
            return None
        return User(id=orm.id, username=orm.username, email=orm.email, hashed_password=orm.hashed_password), api_key.id

    def touch_last_used(self, key_id: int) -> None:
        key = self._session.get(ORMApiKey, key_id)
        if key:
            key.last_used_at = utc_now()
            self._session.add(key)
            self._session.flush()
