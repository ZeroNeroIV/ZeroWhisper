"""In-memory fakes for hexagonal port interfaces — zero database required."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from uuid import UUID

from app.core.domain.category import Category, CategoryType
from app.core.domain.transaction import (
    ExchangeRate,
    Transaction as DomainTransaction,
    TRANSFER_TYPES,
)
from app.core.domain.user import User
from app.core.domain.wallet import Wallet
from app.core.exceptions import NotFoundError, ConflictError
from app.core.ports.category_repo import CategoryRepository
from app.core.ports.exchange_rate_repo import ExchangeRateRepository
from app.core.ports.transaction_repo import TransactionRepository
from app.core.ports.user_repo import UserRepository
from app.core.ports.wallet_repo import WalletRepository


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
        if self.has_children(cat_id, user_id):
            raise ConflictError(f"Category '{cat.name}' has sub-categories")
        del self._store[cat_id]

    def has_children(self, cat_id: UUID, user_id: UUID) -> bool:
        return any(
            c.parent_id == cat_id for c in self._store.values() if c.user_id == user_id
        )

    def get_or_create_transfer_category(self, user_id: UUID) -> Category:
        existing = self.find_by_name(user_id, "Transfer")
        if existing:
            return existing
        cat = Category(user_id=user_id, name="Transfer", type=CategoryType.TRANSFER, is_default=True)
        self._store[cat.id] = cat
        return cat

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
        type: str | None = None,
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
            and (type is None
                 or (t.type.value in TRANSFER_TYPES if type == "transfer" else t.type.value == type))
        ]
        items.sort(key=lambda t: t.transaction_date, reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return items[start:start + page_size], total

    def find_by_transfer_id(self, transfer_id: UUID, user_id: UUID) -> list[DomainTransaction]:
        return [
            t for t in self._store.values()
            if t.transfer_id == transfer_id and t.user_id == user_id and not t.is_deleted
        ]

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
            (t.signed_amount_base for t in self._store.values()
             if t.wallet_id == wallet_id and t.user_id == user_id and not t.is_deleted),
            Decimal("0"),
        )

    def count_by_category_month(self, user_id: UUID, category: str, year: int, month: int) -> int:
        return sum(
            1 for t in self._store.values()
            if t.user_id == user_id and not t.is_deleted and t.category == category
            and t.transaction_date.year == year and t.transaction_date.month == month
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
        types: list[str] | None = None,
    ) -> dict[str, Decimal]:
        result: dict[str, Decimal] = {}
        for t in self._store.values():
            if t.user_id != user_id or t.is_deleted or t.is_transfer:
                continue
            if t.transaction_date.year != year or t.transaction_date.month != month:
                continue
            if exclude_categories and t.category in exclude_categories:
                continue
            if types and t.type.value not in types:
                continue
            result[t.category] = result.get(t.category, Decimal("0")) + t.amount_base
        return result

    def daily_spending_by_category(
        self, user_id: UUID, year: int, month: int,
        exclude_categories: list[str] | None = None,
    ) -> list[tuple[int, str, Decimal]]:
        totals: dict[tuple[int, str], Decimal] = {}
        for t in self._store.values():
            if t.user_id != user_id or t.is_deleted or t.type.value != "expense":
                continue
            if t.transaction_date.year != year or t.transaction_date.month != month:
                continue
            if exclude_categories and t.category in exclude_categories:
                continue
            key = (t.transaction_date.day, t.category)
            totals[key] = totals.get(key, Decimal("0")) + t.amount_base
        return [(day, cat, total) for (day, cat), total in totals.items()]

    def daily_flow(
        self, user_id: UUID, from_date: date, to_date: date,
        exclude_categories: list[str] | None = None,
    ) -> list[tuple[date, Decimal, Decimal]]:
        daily: dict[date, list[Decimal]] = {}
        for t in self._store.values():
            if t.user_id != user_id or t.is_deleted or t.is_transfer:
                continue
            if t.transaction_date < from_date or t.transaction_date > to_date:
                continue
            if exclude_categories and t.category in exclude_categories:
                continue
            entry = daily.setdefault(t.transaction_date, [Decimal("0"), Decimal("0")])
            if t.type.value == "income":
                entry[0] += t.amount_base
            else:
                entry[1] += t.amount_base
        return [(d, income, expenses) for d, (income, expenses) in sorted(daily.items())]

    def monthly_net(self, user_id: UUID) -> list[tuple[str, Decimal]]:
        monthly: dict[str, Decimal] = {}
        for t in self._store.values():
            if t.user_id != user_id or t.is_deleted or t.is_transfer:
                continue
            month = t.transaction_date.strftime("%Y-%m")
            delta = t.amount_base if t.type.value == "income" else -t.amount_base
            monthly[month] = monthly.get(month, Decimal("0")) + delta
        return sorted(monthly.items())

    def totals_by_type(
        self, user_id: UUID, year: int | None = None, month: int | None = None,
        exclude_categories: list[str] | None = None,
    ) -> tuple[Decimal, Decimal]:
        total_income = Decimal("0")
        total_expenses = Decimal("0")
        for t in self._store.values():
            if t.user_id != user_id or t.is_deleted or t.is_transfer:
                continue
            if year is not None and month is not None:
                if t.transaction_date.year != year or t.transaction_date.month != month:
                    continue
            if exclude_categories and t.category in exclude_categories:
                continue
            if t.type.value == "income":
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


class InMemoryWalletRepository(WalletRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Wallet] = {}

    def list_by_user(self, user_id: UUID, include_inactive: bool = False) -> list[Wallet]:
        return [
            w for w in self._store.values()
            if w.user_id == user_id and (include_inactive or w.is_active)
        ]

    def get(self, wallet_id: UUID, user_id: UUID) -> Wallet | None:
        w = self._store.get(wallet_id)
        if w and w.user_id == user_id:
            return w
        return None

    def find_by_name(self, user_id: UUID, name: str) -> Wallet | None:
        needle = name.strip().lower()
        for w in self._store.values():
            if w.user_id == user_id and w.name.lower() == needle:
                return w
        return None

    def save(self, wallet: Wallet) -> Wallet:
        self._store[wallet.id] = wallet
        return wallet

    def update(self, wallet: Wallet) -> Wallet:
        if wallet.id not in self._store:
            raise NotFoundError("Wallet", str(wallet.id))
        self._store[wallet.id] = wallet
        return wallet

    def delete(self, wallet_id: UUID, user_id: UUID) -> bool:
        w = self._store.get(wallet_id)
        if not w or w.user_id != user_id:
            return False
        del self._store[wallet_id]
        return True


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
