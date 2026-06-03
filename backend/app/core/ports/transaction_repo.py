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
    ) -> tuple[list[Transaction], int]:
        """Paginated, filterable list of non-deleted transactions.

        Returns (items, total_count). Page and page_size must be positive.
        """
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
    ) -> dict[str, Decimal]:
        """Aggregate amount_base per category for a given month.

        Returns {category_name: total_amount}. Excludes deleted transactions.
        """
        ...

    @abstractmethod
    def cash_flow(
        self,
        user_id: UUID,
        from_date: date,
        to_date: date,
        income_categories: list[str],
        savings_categories: list[str],
    ) -> list[dict]:
        """Daily income/expense aggregates for date range.

        Returns sorted list of {date, income, expenses, balance} dicts.
        """
        ...

    @abstractmethod
    def net_worth_trend(
        self,
        user_id: UUID,
        income_categories: list[str],
        expense_categories: list[str],
    ) -> list[dict]:
        """Monthly cumulative net worth.

        Returns sorted list of {month: str, net_worth: float} dicts.
        """
        ...

    @abstractmethod
    def monthly_totals_by_type(
        self,
        user_id: UUID,
        year: int,
        month: int,
        type_map: dict[str, str],
        savings_categories: list[str],
    ) -> tuple[Decimal, Decimal]:
        """Total income and total expenses for a month.

        Returns (total_income, total_expenses). Helper for dashboard.
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
