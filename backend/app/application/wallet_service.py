"""
Wallet management use case — CRUD for wallets.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from app.core.domain.wallet import Wallet
from app.core.exceptions import ValidationError
from app.core.ports.wallet_repo import WalletRepository

VALID_CURRENCIES = frozenset({"JOD", "USD"})


class WalletService:

    def __init__(self, repo: WalletRepository) -> None:
        self._repo = repo

    def list_wallets(self, user_id: UUID) -> list[Wallet]:
        return self._repo.list_by_user(user_id)

    def get_wallet(self, wallet_id: UUID, user_id: UUID) -> Wallet | None:
        return self._repo.get(wallet_id, user_id)

    def create(self, user_id: UUID, name: str, currency: str = "JOD",
               initial_balance: Decimal = Decimal("0")) -> Wallet:
        if not name.strip():
            raise ValidationError("Wallet name is required")
        if currency not in VALID_CURRENCIES:
            raise ValidationError(f"Currency must be one of {VALID_CURRENCIES}")
        wallet = Wallet(user_id=user_id, name=name.strip(),
                        currency=currency, balance=initial_balance)
        return self._repo.save(wallet)

    def delete(self, wallet_id: UUID, user_id: UUID) -> bool:
        return self._repo.delete(wallet_id, user_id)
