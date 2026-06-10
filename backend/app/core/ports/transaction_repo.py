"""
TransactionRepository port — abstract persistence contract.

Why a Repository interface instead of direct SQLModel queries?
- Every analytics/mcp/transaction function duplicated the same WHERE filters
- Cannot unit test business logic without a real database
- SQLAlchemy/SQLModel is an implementation detail that should not leak into the domain

Implementations of this interface live in infrastructure/repositories/.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.core.domain.transaction import Transaction


class TransactionRepository(ABC):

    @abstractmethod
    def save(self, tx: Transaction) -> Transaction:
        """Persist a new transaction. Returns the saved entity with generated fields."""
        ...

    @abstractmethod
    def find_by_id(self, tx_id: UUID, user_id: UUID) -> Transaction | None:
        """Find non-deleted transaction by id and user. Returns None if not found."""
        ...

    @abstractmethod
    def find_by_user(
        self,
        user_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        currency: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        source: str | None = None,
        wallet_id: UUID | None = None,
        type: str | None = None,
    ) -> tuple[list[Transaction], int]:
        """Paginated, filterable list of non-deleted transactions.

        Returns (items, total_count). Page and page_size must be positive.
        """
        ...

    @abstractmethod
    def find_by_transfer_id(self, transfer_id: UUID, user_id: UUID) -> list[Transaction]:
        """Both legs of a transfer (non-deleted)."""
        ...

    @abstractmethod
    def soft_delete(self, tx_id: UUID, user_id: UUID) -> None:
        """Mark a transaction as deleted. Raises NotFoundError if not found."""
        ...

    @abstractmethod
    def update(self, tx: Transaction) -> Transaction:
        """Persist changes to an existing transaction."""
        ...

    @abstractmethod
    def sum_by_wallet(self, wallet_id: UUID, user_id: UUID) -> Decimal:
        """Signed sum of amount_base for non-deleted transactions in a wallet.

        Income and incoming transfers add; expenses and outgoing transfers subtract.
        """
        ...

    @abstractmethod
    def count_by_category_month(self, user_id: UUID, category: str, year: int, month: int) -> int:
        """Number of non-deleted transactions in a category for a given month."""
        ...

    @abstractmethod
    def sum_by_categories(
        self,
        user_id: UUID,
        categories: list[str],
    ) -> Decimal:
        """Sum amount_base for non-deleted transactions matching any of the given categories."""
        ...

    @abstractmethod
    def monthly_spending_by_category(
        self,
        user_id: UUID,
        year: int,
        month: int,
        exclude_categories: list[str] | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Decimal]:
        """Aggregate amount_base per category for a given month.

        Returns {category_name: total_amount}. Transfers and deleted rows are
        always excluded; `types` further restricts to the given transaction types.
        """
        ...

    @abstractmethod
    def daily_spending_by_category(
        self,
        user_id: UUID,
        year: int,
        month: int,
        exclude_categories: list[str] | None = None,
    ) -> list[tuple[int, str, Decimal]]:
        """Per-day, per-category expense totals for a month.

        Returns (day_of_month, category, total) tuples for expense-type rows.
        """
        ...

    @abstractmethod
    def daily_flow(
        self,
        user_id: UUID,
        from_date: date,
        to_date: date,
        exclude_categories: list[str] | None = None,
    ) -> list[tuple[date, Decimal, Decimal]]:
        """Daily (date, income, expenses) totals classified by transaction type.

        Sorted by date; transfers excluded.
        """
        ...

    @abstractmethod
    def monthly_net(self, user_id: UUID) -> list[tuple[str, Decimal]]:
        """Per-month net (income - expenses) by transaction type, sorted by month.

        Returns ("YYYY-MM", net) tuples; transfers excluded.
        """
        ...

    @abstractmethod
    def totals_by_type(
        self,
        user_id: UUID,
        year: int | None = None,
        month: int | None = None,
        exclude_categories: list[str] | None = None,
    ) -> tuple[Decimal, Decimal]:
        """(total_income, total_expenses) classified by transaction type.

        Scoped to a month when year+month given, lifetime otherwise.
        """
        ...

    @abstractmethod
    def recent(
        self,
        user_id: UUID,
        limit: int = 5,
    ) -> list[Transaction]:
        """Most recent non-deleted transactions, newest first."""
        ...
