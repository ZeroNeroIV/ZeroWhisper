"""In-memory fakes for hexagonal port interfaces — zero database required."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.domain.category import Category, CategoryType
from app.core.domain.transaction import ExchangeRate, Transaction as DomainTransaction
from app.core.domain.user import User
from app.core.exceptions import NotFoundError, ConflictError
from app.core.ports.category_repo import CategoryRepository
from app.core.ports.exchange_rate_repo import ExchangeRateRepository
from app.core.ports.transaction_repo import TransactionRepository
from app.core.ports.user_repo import UserRepository


class InMemoryCategoryRepository(CategoryRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Category] = {}
        self._seeded = False

    def find_by_user(self, user_id: UUID) -> list[Category]:
        return [c for c in self._store.values() if c.user_id == user_id]

    def find_by_id(self, cat_id: UUID, user_id: UUID) -> Category | None:
        c = self._store.get(cat_id)
        if c and c.user_id == user_id:
            return c
        return None

    def find_by_name(self, user_id: UUID, name: str) -> Category | None:
        for c in self._store.values():
            if c.user_id == user_id and c.name == name:
                return c
        return None

    def save(self, cat: Category) -> Category:
        self._store[cat.id] = cat
        return cat

    def update(self, cat: Category) -> Category:
        existing = self._store.get(cat.id)
        if not existing:
            raise NotFoundError("Category", str(cat.id))
        self._store[cat.id] = cat
        return cat

    def delete(self, cat_id: UUID, user_id: UUID) -> None:
        cat = self._store.get(cat_id)
        if not cat or cat.user_id != user_id:
            raise NotFoundError("Category", str(cat_id))
        del self._store[cat_id]

    def get_type_map(self, user_id: UUID) -> dict[str, str]:
        return {c.name: c.type.value for c in self.find_by_user(user_id)}

    def find_by_type(self, user_id: UUID, type: CategoryType) -> list[Category]:
        return [c for c in self._store.values() if c.user_id == user_id and c.type == type]

    def seed_defaults(self, user_id: UUID) -> list[Category]:
        if self._seeded:
            return self.find_by_user(user_id)
        defaults = [
            Category(user_id=user_id, name="Food", type=CategoryType.EXPENSE, is_default=True),
            Category(user_id=user_id, name="Income", type=CategoryType.INCOME, is_default=True),
            Category(user_id=user_id, name="Savings", type=CategoryType.SAVINGS, is_default=True),
        ]
        for c in defaults:
            self._store[c.id] = c
        self._seeded = True
        return defaults


class InMemoryTransactionRepository(TransactionRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, DomainTransaction] = {}
        self._next_id: int = 1

    def save(self, tx: DomainTransaction) -> DomainTransaction:
        self._store[tx.id] = tx
        return tx

    def find_by_id(self, tx_id: UUID, user_id: UUID) -> DomainTransaction | None:
        tx = self._store.get(tx_id)
        if tx and tx.user_id == user_id and not tx.is_deleted:
            return tx
        return None

    def find_by_user(
        self, user_id: UUID, *, page: int = 1, page_size: int = 20,
        category: str | None = None, currency: str | None = None,
        date_from: date | None = None, date_to: date | None = None,
        source: str | None = None, wallet_id: UUID | None = None,
    ) -> tuple[list[DomainTransaction], int]:
        items = [
            t for t in self._store.values()
            if t.user_id == user_id and not t.is_deleted
            and (category is None or t.category == category)
            and (currency is None or t.currency_original == currency)
            and (date_from is None or t.transaction_date >= date_from)
            and (date_to is None or t.transaction_date <= date_to)
            and (source is None or t.source == source)
            and (wallet_id is None or t.wallet_id == wallet_id)
        ]
        items.sort(key=lambda t: t.transaction_date, reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return items[start:start + page_size], total

    def soft_delete(self, tx_id: UUID, user_id: UUID) -> None:
        tx = self._store.get(tx_id)
        if not tx or tx.user_id != user_id:
            raise NotFoundError("Transaction", str(tx_id))
        tx.is_deleted = True

    def update(self, tx: DomainTransaction) -> DomainTransaction:
        existing = self._store.get(tx.id)
        if not existing:
            raise NotFoundError("Transaction", str(tx.id))
        self._store[tx.id] = tx
        return tx

    def sum_by_wallet(self, wallet_id: UUID, user_id: UUID) -> Decimal:
        return sum(
            (t.amount_base for t in self._store.values()
             if t.wallet_id == wallet_id and t.user_id == user_id and not t.is_deleted),
            Decimal("0"),
        )

    def sum_by_categories(self, user_id: UUID, categories: list[str]) -> Decimal:
        return sum(
            (t.amount_base for t in self._store.values()
             if t.user_id == user_id and not t.is_deleted and t.category in categories),
            Decimal("0"),
        )

    def monthly_spending_by_category(
        self, user_id: UUID, year: int, month: int,
        exclude_categories: list[str] | None = None,
    ) -> dict[str, Decimal]:
        result: dict[str, Decimal] = {}
        for t in self._store.values():
            if t.user_id != user_id or t.is_deleted:
                continue
            if t.transaction_date.year != year or t.transaction_date.month != month:
                continue
            if exclude_categories and t.category in exclude_categories:
                continue
            result[t.category] = result.get(t.category, Decimal("0")) + t.amount_base
        return result

    def cash_flow(
        self, user_id: UUID, from_date: date, to_date: date,
        income_categories: list[str], savings_categories: list[str],
    ) -> list[dict]:
        exclude = set(income_categories) | set(savings_categories)
        daily: dict[date, dict[str, Any]] = {}
        for t in self._store.values():
            if t.user_id != user_id or t.is_deleted:
                continue
            if t.transaction_date < from_date or t.transaction_date > to_date:
                continue
            d = t.transaction_date
            if d not in daily:
                daily[d] = {"date": str(d), "income": 0.0, "expenses": 0.0}
            if t.category in income_categories:
                daily[d]["income"] += float(t.amount_base)
            elif t.category not in exclude:
                daily[d]["expenses"] += float(t.amount_base)
        result = sorted(daily.values(), key=lambda x: x["date"])
        running = 0.0
        for day in result:
            running += day["income"] - day["expenses"]
            day["balance"] = round(running, 2)
            day["income"] = round(day["income"], 2)
            day["expenses"] = round(day["expenses"], 2)
        return result

    def net_worth_trend(
        self, user_id: UUID,
        income_categories: list[str], expense_categories: list[str],
    ) -> list[dict]:
        monthly: dict[str, float] = {}
        for t in self._store.values():
            if t.user_id != user_id or t.is_deleted:
                continue
            month = t.transaction_date.strftime("%Y-%m")
            delta = float(t.amount_base) if t.category in income_categories else -float(t.amount_base)
            monthly[month] = monthly.get(month, 0.0) + delta
        cumulative = 0.0
        result: list[dict] = []
        for month in sorted(monthly):
            cumulative += monthly[month]
            result.append({"month": month, "net_worth": round(cumulative, 2)})
        return result

    def monthly_totals_by_type(
        self, user_id: UUID, year: int, month: int,
        type_map: dict[str, str], savings_categories: list[str],
    ) -> tuple[Decimal, Decimal]:
        total_income = Decimal("0")
        total_expenses = Decimal("0")
        for t in self._store.values():
            if t.user_id != user_id or t.is_deleted:
                continue
            if t.transaction_date.year != year or t.transaction_date.month != month:
                continue
            if t.category in savings_categories:
                continue
            if type_map.get(t.category) == "income":
                total_income += t.amount_base
            else:
                total_expenses += t.amount_base
        return total_income, total_expenses

    def recent(self, user_id: UUID, limit: int = 5) -> list[DomainTransaction]:
        items = sorted(
            [t for t in self._store.values() if t.user_id == user_id and not t.is_deleted],
            key=lambda t: t.created_at,
            reverse=True,
        )
        return items[:limit]


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, User] = {}

    def find_by_id(self, user_id: UUID) -> User | None:
        return self._store.get(user_id)

    def find_by_username(self, username: str) -> User | None:
        for u in self._store.values():
            if u.username == username:
                return u
        return None

    def find_by_username_or_email(self, username: str, email: str) -> User | None:
        for u in self._store.values():
            if u.username == username or u.email == email:
                return u
        return None

    def save(self, user: User) -> User:
        self._store[user.id] = user
        return user


class InMemoryExchangeRateRepository(ExchangeRateRepository):
    def __init__(self) -> None:
        self._store: list[ExchangeRate] = []

    def set_rate(self, rate: Decimal, for_date: date, source: str = "manual") -> ExchangeRate:
        r = ExchangeRate(date=for_date, jod_per_usd=rate, source=source)
        self._store.append(r)
        return r

    def get_rate(self, for_date: date) -> ExchangeRate | None:
        candidates = [r for r in self._store if r.date <= for_date]
        if not candidates:
            return None
        return max(candidates, key=lambda r: r.date)

    def get_current(self) -> ExchangeRate | None:
        if not self._store:
            return None
        return max(self._store, key=lambda r: r.date)

    def get_history(self, limit: int = 30) -> list[ExchangeRate]:
        return sorted(self._store, key=lambda r: r.date, reverse=True)[:limit]
