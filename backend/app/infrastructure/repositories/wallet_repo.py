"""
SQLModel-backed WalletRepository implementation.
"""
from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, func, select

from app.core.domain.wallet import Wallet as DomainWallet, WalletType
from app.core.exceptions import NotFoundError
from app.core.ports.wallet_repo import WalletRepository
from app.models.wallet import Wallet as ORMWallet


def _to_domain(orm: ORMWallet) -> DomainWallet:
    return DomainWallet(
        id=orm.id, user_id=orm.user_id, name=orm.name,
        type=WalletType(orm.type), currency=orm.currency,
        balance=orm.balance, initial_balance=orm.initial_balance,
        icon=orm.icon, is_active=orm.is_active, created_at=orm.created_at,
    )


def _to_orm(domain: DomainWallet) -> ORMWallet:
    return ORMWallet(
        id=domain.id, user_id=domain.user_id, name=domain.name,
        type=domain.type.value, currency=domain.currency,
        balance=domain.balance, initial_balance=domain.initial_balance,
        icon=domain.icon, is_active=domain.is_active, created_at=domain.created_at,
    )


class SQLModelWalletRepository(WalletRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_user(self, user_id: UUID, include_inactive: bool = False) -> list[DomainWallet]:
        query = select(ORMWallet).where(ORMWallet.user_id == user_id)
        if not include_inactive:
            query = query.where(ORMWallet.is_active == True)
        rows = self._session.exec(query.order_by(ORMWallet.created_at)).all()
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

    def find_by_name(self, user_id: UUID, name: str) -> DomainWallet | None:
        row = self._session.exec(
            select(ORMWallet).where(
                ORMWallet.user_id == user_id,
                func.lower(ORMWallet.name) == name.strip().lower(),
            )
        ).first()
        return _to_domain(row) if row else None

    def save(self, wallet: DomainWallet) -> DomainWallet:
        orm = _to_orm(wallet)
        self._session.add(orm)
        self._session.flush()
        self._session.refresh(orm)
        return _to_domain(orm)

    def update(self, wallet: DomainWallet) -> DomainWallet:
        orm = self._session.exec(
            select(ORMWallet).where(
                ORMWallet.id == wallet.id,
                ORMWallet.user_id == wallet.user_id,
            )
        ).first()
        if not orm:
            raise NotFoundError("Wallet", str(wallet.id))
        orm.name = wallet.name
        orm.type = wallet.type.value
        orm.currency = wallet.currency
        orm.icon = wallet.icon
        orm.initial_balance = wallet.initial_balance
        orm.is_active = wallet.is_active
        self._session.add(orm)
        self._session.flush()
        self._session.refresh(orm)
        return _to_domain(orm)

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
        self._session.flush()
        return True
