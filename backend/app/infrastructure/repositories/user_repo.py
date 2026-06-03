from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select, or_

from app.core.domain.user import User as DomainUser
from app.core.ports.user_repo import UserRepository
from app.models.user import User as ORMUser


class SQLModelUserRepository(UserRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: ORMUser) -> DomainUser:
        return DomainUser(
            id=orm.id,
            username=orm.username,
            email=orm.email,
            hashed_password=orm.hashed_password,
            is_admin=orm.is_admin,
            created_at=orm.created_at,
        )

    @staticmethod
    def _to_orm(domain: DomainUser) -> ORMUser:
        return ORMUser(
            id=domain.id,
            username=domain.username,
            email=domain.email,
            hashed_password=domain.hashed_password,
            is_admin=domain.is_admin,
            created_at=domain.created_at,
        )

    def find_by_id(self, user_id: UUID) -> DomainUser | None:
        orm = self._session.get(ORMUser, str(user_id))
        return self._to_domain(orm) if orm else None

    def find_by_username(self, username: str) -> DomainUser | None:
        from sqlmodel import select
        orm = self._session.exec(
            select(ORMUser).where(ORMUser.username == username)
        ).first()
        return self._to_domain(orm) if orm else None

    def find_by_username_or_email(self, username: str, email: str) -> DomainUser | None:
        from sqlmodel import select
        orm = self._session.exec(
            select(ORMUser).where(
                (ORMUser.username == username) | (ORMUser.email == email)
            )
        ).first()
        return self._to_domain(orm) if orm else None

    def save(self, user: DomainUser) -> DomainUser:
        orm = self._to_orm(user)
        self._session.add(orm)
        self._session.commit()
        self._session.refresh(orm)
        return self._to_domain(orm)
