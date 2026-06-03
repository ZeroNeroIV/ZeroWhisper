"""
Wallet management use case — CRUD for wallets with balance recalculation.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from app.core.domain.wallet import Wallet
from app.core.exceptions import NotFoundError, ValidationError
from app.core.ports.transaction_repo import TransactionRepository
from app.core.ports.wallet_repo import WalletRepository

VALID_CURRENCIES = frozenset({"JOD", "USD"})


class WalletService:

    def __init__(self, repo: WalletRepository,
                 tx_repo: TransactionRepository) -> None:
        self._repo = repo
        self._tx_repo = tx_repo

    def list_wallets(self, user_id: UUID) -> list[Wallet]:
        wallets = self._repo.list_by_user(user_id)
        for w in wallets:
            w.balance = self.recalculate_balance(w.id, user_id)
            self._repo.update_balance(w.id, w.balance)
        return wallets

    def get_wallet(self, wallet_id: UUID, user_id: UUID) -> Wallet | None:
        w = self._repo.get(wallet_id, user_id)
        if w is None:
            return None
        w.balance = self.recalculate_balance(w.id, user_id)
        self._repo.update_balance(w.id, w.balance)
        return w

    def recalculate_balance(self, wallet_id: UUID, user_id: UUID) -> Decimal:
        return self._tx_repo.sum_by_wallet(wallet_id, user_id)

    def create(self, user_id: UUID, name: str, currency: str = "JOD",
               initial_balance: Decimal = Decimal("0")) -> Wallet:
        if not name.strip():
            raise ValidationError("Wallet name is required")
        if currency not in VALID_CURRENCIES:
            raise ValidationError(f"Currency must be one of {VALID_CURRENCIES}")
        wallet = Wallet(user_id=user_id, name=name.strip(),
                        currency=currency, balance=Decimal("0"))
        w = self._repo.save(wallet)
        if initial_balance > 0:
            w.balance = initial_balance
            self._repo.update_balance(w.id, initial_balance)
            w.balance = initial_balance
        return w

    def delete(self, wallet_id: UUID, user_id: UUID) -> bool:
        return self._repo.delete(wallet_id, user_id)
