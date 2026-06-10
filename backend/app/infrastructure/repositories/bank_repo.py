"""
SQLModel-backed BankConnectionRepository implementation.
"""
from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.core.ports.bank_repo import BankConnectionData, BankConnectionRepository
from app.models.bank import BankConnection as ORMBankConnection


def _to_data(orm: ORMBankConnection) -> BankConnectionData:
    return BankConnectionData(
        id=orm.id, bank_name=orm.bank_name, auth_type=orm.auth_type,
        account_number=orm.account_number or "",
        is_active=orm.is_active, last_sync_at=orm.last_sync_at,
        created_at=orm.created_at, credentials=orm.credentials or {},
        user_id=orm.user_id,
    )


class SQLModelBankConnectionRepository(BankConnectionRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_user(self, user_id: UUID) -> list[BankConnectionData]:
        rows = self._session.exec(
            select(ORMBankConnection).where(ORMBankConnection.user_id == user_id)
        ).all()
        return [_to_data(r) for r in rows]

    def get(self, conn_id: int, user_id: UUID) -> BankConnectionData | None:
        row = self._session.exec(
            select(ORMBankConnection).where(
                ORMBankConnection.id == conn_id,
                ORMBankConnection.user_id == user_id,
            )
        ).first()
        if row is None:
            return None
        return _to_data(row)

    def create(self, user_id: UUID, bank_name: str, auth_type: str,
               account_number: str, credentials: dict) -> BankConnectionData:
        orm = ORMBankConnection(
            user_id=user_id, bank_name=bank_name, auth_type=auth_type,
            account_number=account_number, credentials=credentials,
        )
        self._session.add(orm)
        self._session.commit()
        self._session.refresh(orm)
        return _to_data(orm)

    def update(self, conn_id: int, user_id: UUID, **kwargs) -> BankConnectionData | None:
        row = self._session.exec(
            select(ORMBankConnection).where(
                ORMBankConnection.id == conn_id,
                ORMBankConnection.user_id == user_id,
            )
        ).first()
        if row is None:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(row, key, value)
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_data(row)

    def delete(self, conn_id: int, user_id: UUID) -> bool:
        row = self._session.exec(
            select(ORMBankConnection).where(
                ORMBankConnection.id == conn_id,
                ORMBankConnection.user_id == user_id,
            )
        ).first()
        if row is None:
            return False
        self._session.delete(row)
        self._session.commit()
        return True
