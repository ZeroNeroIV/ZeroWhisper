"""
Wallet management use case — CRUD for wallets with derived balances.

A wallet's balance is always `initial_balance + signed sum of its
transactions` (income and incoming transfers add, expenses and outgoing
transfers subtract). The stored `balance` column is just a cache refreshed
on read.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from app.core.domain.wallet import Wallet, WalletType
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.ports.transaction_repo import TransactionRepository
from app.core.ports.wallet_repo import WalletRepository

VALID_CURRENCIES = frozenset({"JOD", "USD"})


class WalletService:

    def __init__(self, repo: WalletRepository,
                 tx_repo: TransactionRepository) -> None:
        self._repo = repo
        self._tx_repo = tx_repo

    def list_wallets(self, user_id: UUID, include_inactive: bool = False) -> list[Wallet]:
        wallets = self._repo.list_by_user(user_id, include_inactive=include_inactive)
        for w in wallets:
            self._refresh_balance(w)
        return wallets

    def get_wallet(self, wallet_id: UUID, user_id: UUID) -> Wallet | None:
        w = self._repo.get(wallet_id, user_id)
        if w is None:
            return None
        self._refresh_balance(w)
        return w

    def find_by_name(self, user_id: UUID, name: str) -> Wallet | None:
        w = self._repo.find_by_name(user_id, name)
        if w is not None:
            self._refresh_balance(w)
        return w

    def _refresh_balance(self, wallet: Wallet) -> None:
        balance = wallet.initial_balance + self._tx_repo.sum_by_wallet(wallet.id, wallet.user_id)
        if balance != wallet.balance:
            self._repo.update_balance(wallet.id, balance)
        wallet.balance = balance

    def create(
        self,
        user_id: UUID,
        name: str,
        type: WalletType = WalletType.CASH,
        currency: str = "JOD",
        initial_balance: Decimal = Decimal("0"),
        icon: str | None = None,
    ) -> Wallet:
        name = name.strip()
        if not name:
            raise ValidationError("Wallet name is required")
        if currency not in VALID_CURRENCIES:
            raise ValidationError(f"Currency must be one of {VALID_CURRENCIES}")
        if self._repo.find_by_name(user_id, name):
            raise ConflictError(f"A wallet named '{name}' already exists")
        wallet = Wallet(
            user_id=user_id, name=name, type=type, currency=currency,
            balance=initial_balance, initial_balance=initial_balance, icon=icon,
        )
        return self._repo.save(wallet)

    def update(
        self,
        wallet_id: UUID,
        user_id: UUID,
        *,
        name: str | None = None,
        type: WalletType | None = None,
        currency: str | None = None,
        initial_balance: Decimal | None = None,
        icon: str | None = None,
        is_active: bool | None = None,
    ) -> Wallet:
        wallet = self._repo.get(wallet_id, user_id)
        if wallet is None:
            raise NotFoundError("Wallet", str(wallet_id))
        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationError("Wallet name is required")
            existing = self._repo.find_by_name(user_id, name)
            if existing and existing.id != wallet_id:
                raise ConflictError(f"A wallet named '{name}' already exists")
            wallet.name = name
        if type is not None:
            wallet.type = type
        if currency is not None:
            if currency not in VALID_CURRENCIES:
                raise ValidationError(f"Currency must be one of {VALID_CURRENCIES}")
            wallet.currency = currency
        if initial_balance is not None:
            wallet.initial_balance = initial_balance
        if icon is not None:
            wallet.icon = icon
        if is_active is not None:
            wallet.is_active = is_active
        updated = self._repo.update(wallet)
        self._refresh_balance(updated)
        return updated

    def delete(self, wallet_id: UUID, user_id: UUID) -> bool:
        wallet = self._repo.get(wallet_id, user_id)
        if wallet is None:
            return False
        txs, total = self._tx_repo.find_by_user(user_id, page=1, page_size=1, wallet_id=wallet_id)
        if total > 0:
            raise ConflictError(
                f"Wallet '{wallet.name}' has {total} transaction(s). Archive it instead of deleting."
            )
        return self._repo.delete(wallet_id, user_id)
