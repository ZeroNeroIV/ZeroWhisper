"""
WalletRepository port — abstract persistence contract for wallets.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import UUID

from app.core.domain.wallet import Wallet


class WalletRepository(ABC):

    @abstractmethod
    def list_by_user(self, user_id: UUID, include_inactive: bool = False) -> list[Wallet]:
        ...

    @abstractmethod
    def get(self, wallet_id: UUID, user_id: UUID) -> Wallet | None:
        ...

    @abstractmethod
    def find_by_name(self, user_id: UUID, name: str) -> Wallet | None:
        """Case-insensitive lookup by wallet name."""
        ...

    @abstractmethod
    def save(self, wallet: Wallet) -> Wallet:
        ...

    @abstractmethod
    def update(self, wallet: Wallet) -> Wallet:
        """Persist changes to name/type/currency/icon/initial_balance/is_active."""
        ...

    @abstractmethod
    def update_balance(self, wallet_id: UUID, balance: Decimal) -> None:
        ...

    @abstractmethod
    def delete(self, wallet_id: UUID, user_id: UUID) -> bool:
        ...
