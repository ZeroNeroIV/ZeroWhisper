"""
SQLModel-backed WalletRepository implementation.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlmodel import Session, select

from app.core.domain.wallet import Wallet as DomainWallet
from app.core.ports.wallet_repo import WalletRepository
from app.models.wallet import Wallet as ORMWallet


def _to_domain(orm: ORMWallet) -> DomainWallet:
    return DomainWallet(
        id=orm.id, user_id=orm.user_id, name=orm.name,
        currency=orm.currency, balance=orm.balance,
        is_active=orm.is_active, created_at=orm.created_at,
    )


def _to_orm(domain: DomainWallet) -> ORMWallet:
    return ORMWallet(
        id=domain.id, user_id=domain.user_id, name=domain.name,
        currency=domain.currency, balance=domain.balance,
        is_active=domain.is_active, created_at=domain.created_at,
    )


class SQLModelWalletRepository(WalletRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_user(self, user_id: UUID) -> list[DomainWallet]:
        rows = self._session.exec(
            select(ORMWallet).where(ORMWallet.user_id == user_id)
        ).all()
        return [_to_domain(r) for r in rows]

    def get(self, wallet_id: UUID, user_id: UUID) -> DomainWallet | None:
        row = self._session.exec(
            select(ORMWallet).where(
                ORMWallet.id == wallet_id,
                ORMWallet.user_id == user_id,
            )
        ).first()
        if row is None:
            return None
        return _to_domain(row)

    def save(self, wallet: DomainWallet) -> DomainWallet:
        orm = _to_orm(wallet)
        self._session.add(orm)
        self._session.commit()
        self._session.refresh(orm)
        return _to_domain(orm)

    def update_balance(self, wallet_id: UUID, balance: Decimal) -> None:
        orm = self._session.get(ORMWallet, wallet_id)
        if orm:
            orm.balance = balance
            self._session.add(orm)
            self._session.commit()

    def delete(self, wallet_id: UUID, user_id: UUID) -> bool:
        row = self._session.exec(
            select(ORMWallet).where(
                ORMWallet.id == wallet_id,
                ORMWallet.user_id == user_id,
            )
        ).first()
        if not row:
            return False
        self._session.delete(row)
        self._session.commit()
        return True
