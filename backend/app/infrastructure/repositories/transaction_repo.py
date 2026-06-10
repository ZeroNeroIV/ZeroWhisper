"""
SQLModel-backed TransactionRepository implementation.

Translates between core/domain Transaction objects and the SQLModel ORM
table models. Every method maps cleanly to the port interface — no business
logic, no validation beyond what the domain model enforces.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case
from sqlmodel import Session, select, func

from app.core.domain.transaction import Transaction as DomainTransaction, TransactionType, TRANSFER_TYPES
from app.core.exceptions import NotFoundError
from app.core.ports.transaction_repo import TransactionRepository
from app.models.transaction import Transaction as ORMTransaction

# Income and incoming transfers add to a wallet; everything else subtracts.
_POSITIVE_TYPES = (TransactionType.INCOME.value, TransactionType.TRANSFER_IN.value)


class SQLModelTransactionRepository(TransactionRepository):
    """Concrete repository backed by SQLModel ORM."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Helpers ───────────────────────────────────────────────────────────────────

    @staticmethod
    def _to_domain(orm: ORMTransaction) -> DomainTransaction:
        return DomainTransaction(
            id=orm.id,
            user_id=orm.user_id,
            amount_original=orm.amount_original,
            currency_original=orm.currency_original,
            amount_base=orm.amount_base,
            exchange_rate=orm.exchange_rate,
            category=orm.category,
            description=orm.description,
            transaction_date=orm.transaction_date,
            source=orm.source,
            type=TransactionType(orm.type),
            is_deleted=orm.is_deleted,
            wallet_id=orm.wallet_id,
            transfer_id=orm.transfer_id,
            created_at=orm.created_at,
        )

    @staticmethod
    def _to_orm(domain: DomainTransaction) -> ORMTransaction:
        return ORMTransaction(
            id=domain.id,
            user_id=domain.user_id,
            amount_original=domain.amount_original,
            currency_original=domain.currency_original,
            amount_base=domain.amount_base,
            exchange_rate=domain.exchange_rate,
            category=domain.category,
            description=domain.description,
            transaction_date=domain.transaction_date,
            source=domain.source,
            type=domain.type.value,
            is_deleted=domain.is_deleted,
            wallet_id=domain.wallet_id,
            transfer_id=domain.transfer_id,
            created_at=domain.created_at,
        )

    def _apply_user_filter(self, query, user_id: UUID):
        return query.where(
            ORMTransaction.user_id == user_id,
            ORMTransaction.is_deleted == False,
        )

    # ── Interface ─────────────────────────────────────────────────────────────────

    def save(self, tx: DomainTransaction) -> DomainTransaction:
        orm = self._to_orm(tx)
        self._session.add(orm)
        self._session.flush()
        self._session.refresh(orm)
        return self._to_domain(orm)

    def find_by_id(self, tx_id: UUID, user_id: UUID) -> DomainTransaction | None:
        result = self._session.exec(
            select(ORMTransaction).where(
                ORMTransaction.id == tx_id,
                ORMTransaction.user_id == user_id,
                ORMTransaction.is_deleted == False,
            )
        ).first()
        return self._to_domain(result) if result else None

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
    ) -> tuple[list[DomainTransaction], int]:
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20

        query = select(ORMTransaction).where(
            ORMTransaction.user_id == user_id,
            ORMTransaction.is_deleted == False,
        )
        if category:
            query = query.where(ORMTransaction.category == category)
        if currency:
            query = query.where(ORMTransaction.currency_original == currency)
        if date_from:
            query = query.where(ORMTransaction.transaction_date >= date_from)
        if date_to:
            query = query.where(ORMTransaction.transaction_date <= date_to)
        if source:
            query = query.where(ORMTransaction.source == source)
        if wallet_id:
            query = query.where(ORMTransaction.wallet_id == wallet_id)
        if type:
            if type == "transfer":
                query = query.where(ORMTransaction.type.in_(TRANSFER_TYPES))
            else:
                query = query.where(ORMTransaction.type == type)

        count_query = select(func.count()).select_from(query.subquery())
        total = self._session.exec(count_query).one()

        items = self._session.exec(
            query.order_by(ORMTransaction.transaction_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return [self._to_domain(t) for t in items], total

    def soft_delete(self, tx_id: UUID, user_id: UUID) -> None:
        orm = self._session.exec(
            select(ORMTransaction).where(
                ORMTransaction.id == tx_id,
                ORMTransaction.user_id == user_id,
                ORMTransaction.is_deleted == False,
            )
        ).first()
        if not orm:
            raise NotFoundError("Transaction", str(tx_id))
        orm.is_deleted = True
        self._session.add(orm)
        self._session.flush()

    def update(self, tx: DomainTransaction) -> DomainTransaction:
        orm = self._session.exec(
            select(ORMTransaction).where(
                ORMTransaction.id == tx.id,
                ORMTransaction.user_id == tx.user_id,
            )
        ).first()
        if not orm:
            raise NotFoundError("Transaction", str(tx.id))
        orm.amount_original = tx.amount_original
        orm.currency_original = tx.currency_original
        orm.amount_base = tx.amount_base
        orm.exchange_rate = tx.exchange_rate
        orm.category = tx.category
        orm.description = tx.description
        orm.transaction_date = tx.transaction_date
        orm.wallet_id = tx.wallet_id
        orm.type = tx.type.value
        self._session.add(orm)
        self._session.flush()
        self._session.refresh(orm)
        return self._to_domain(orm)

    def find_by_transfer_id(self, transfer_id: UUID, user_id: UUID) -> list[DomainTransaction]:
        items = self._session.exec(
            select(ORMTransaction).where(
                ORMTransaction.transfer_id == transfer_id,
                ORMTransaction.user_id == user_id,
                ORMTransaction.is_deleted == False,
            )
        ).all()
        return [self._to_domain(t) for t in items]

    def sum_by_wallet(self, wallet_id: UUID, user_id: UUID) -> Decimal:
        signed = case(
            (ORMTransaction.type.in_(_POSITIVE_TYPES), ORMTransaction.amount_base),
            else_=-ORMTransaction.amount_base,
        )
        result = self._session.exec(
            select(func.sum(signed)).where(
                ORMTransaction.wallet_id == wallet_id,
                ORMTransaction.user_id == user_id,
                ORMTransaction.is_deleted == False,
            )
        ).one()
        return Decimal(str(result)) if result is not None else Decimal("0")

    def count_by_category_month(self, user_id: UUID, category: str, year: int, month: int) -> int:
        from datetime import date as _date
        month_start = _date(year, month, 1)
        month_end = _date(year + 1, 1, 1) if month == 12 else _date(year, month + 1, 1)
        result = self._session.exec(
            select(func.count()).select_from(ORMTransaction).where(
                ORMTransaction.user_id == user_id,
                ORMTransaction.category == category,
                ORMTransaction.is_deleted == False,
                ORMTransaction.transaction_date >= month_start,
                ORMTransaction.transaction_date < month_end,
            )
        ).one()
        return int(result)

    def sum_by_categories(self, user_id: UUID, categories: list[str]) -> Decimal:
        if not categories:
            return Decimal("0")
        result = self._session.exec(
            select(func.sum(ORMTransaction.amount_base)).where(
                ORMTransaction.user_id == user_id,
                ORMTransaction.is_deleted == False,
                ORMTransaction.category.in_(categories),
            )
        ).one()
        return result or Decimal("0")

    @staticmethod
    def _month_bounds(year: int, month: int) -> tuple[date, date]:
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        return start, end

    def monthly_spending_by_category(
        self,
        user_id: UUID,
        year: int,
        month: int,
        exclude_categories: list[str] | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Decimal]:
        month_start, month_end = self._month_bounds(year, month)

        query = select(
            ORMTransaction.category,
            func.sum(ORMTransaction.amount_base).label("total"),
        ).where(
            ORMTransaction.user_id == user_id,
            ORMTransaction.is_deleted == False,
            ORMTransaction.type.notin_(TRANSFER_TYPES),
            ORMTransaction.transaction_date >= month_start,
            ORMTransaction.transaction_date < month_end,
        )
        if exclude_categories:
            query = query.where(ORMTransaction.category.notin_(exclude_categories))
        if types:
            query = query.where(ORMTransaction.type.in_(types))
        query = query.group_by(ORMTransaction.category)

        return {cat: total for cat, total in self._session.exec(query).all()}

    def daily_spending_by_category(
        self,
        user_id: UUID,
        year: int,
        month: int,
        exclude_categories: list[str] | None = None,
    ) -> list[tuple[int, str, Decimal]]:
        month_start, month_end = self._month_bounds(year, month)

        query = (
            select(
                ORMTransaction.transaction_date,
                ORMTransaction.category,
                func.sum(ORMTransaction.amount_base).label("total"),
            )
            .where(
                ORMTransaction.user_id == user_id,
                ORMTransaction.is_deleted == False,
                ORMTransaction.type == TransactionType.EXPENSE.value,
                ORMTransaction.transaction_date >= month_start,
                ORMTransaction.transaction_date < month_end,
            )
            .group_by(ORMTransaction.transaction_date, ORMTransaction.category)
        )
        if exclude_categories:
            query = query.where(ORMTransaction.category.notin_(exclude_categories))

        return [
            (tx_date.day, category, total)
            for tx_date, category, total in self._session.exec(query).all()
        ]

    def daily_flow(
        self,
        user_id: UUID,
        from_date: date,
        to_date: date,
        exclude_categories: list[str] | None = None,
    ) -> list[tuple[date, Decimal, Decimal]]:
        query = (
            select(
                ORMTransaction.transaction_date,
                ORMTransaction.type,
                func.sum(ORMTransaction.amount_base).label("total"),
            )
            .where(
                ORMTransaction.user_id == user_id,
                ORMTransaction.is_deleted == False,
                ORMTransaction.type.notin_(TRANSFER_TYPES),
                ORMTransaction.transaction_date >= from_date,
                ORMTransaction.transaction_date <= to_date,
            )
            .group_by(ORMTransaction.transaction_date, ORMTransaction.type)
            .order_by(ORMTransaction.transaction_date)
        )
        if exclude_categories:
            query = query.where(ORMTransaction.category.notin_(exclude_categories))

        daily: dict[date, list[Decimal]] = {}
        for tx_date, tx_type, total in self._session.exec(query).all():
            entry = daily.setdefault(tx_date, [Decimal("0"), Decimal("0")])
            if tx_type == TransactionType.INCOME.value:
                entry[0] += total
            else:
                entry[1] += total
        return [(d, income, expenses) for d, (income, expenses) in sorted(daily.items())]

    def monthly_net(self, user_id: UUID) -> list[tuple[str, Decimal]]:
        signed = case(
            (ORMTransaction.type == TransactionType.INCOME.value, ORMTransaction.amount_base),
            else_=-ORMTransaction.amount_base,
        )
        month_expr = func.strftime("%Y-%m", ORMTransaction.transaction_date)
        rows = self._session.exec(
            select(month_expr.label("month"), func.sum(signed).label("net"))
            .where(
                ORMTransaction.user_id == user_id,
                ORMTransaction.is_deleted == False,
                ORMTransaction.type.notin_(TRANSFER_TYPES),
            )
            .group_by(month_expr)
            .order_by(month_expr)
        ).all()
        return [(month, net) for month, net in rows]

    def totals_by_type(
        self,
        user_id: UUID,
        year: int | None = None,
        month: int | None = None,
        exclude_categories: list[str] | None = None,
    ) -> tuple[Decimal, Decimal]:
        """(total_income, total_expenses) classified by the transaction's own type.

        Limited to one month when year+month are given, lifetime otherwise.
        """
        query = select(
            ORMTransaction.type,
            func.sum(ORMTransaction.amount_base).label("total"),
        ).where(
            ORMTransaction.user_id == user_id,
            ORMTransaction.is_deleted == False,
            ORMTransaction.type.notin_(TRANSFER_TYPES),
        )
        if year is not None and month is not None:
            month_start, month_end = self._month_bounds(year, month)
            query = query.where(
                ORMTransaction.transaction_date >= month_start,
                ORMTransaction.transaction_date < month_end,
            )
        if exclude_categories:
            query = query.where(ORMTransaction.category.notin_(exclude_categories))
        query = query.group_by(ORMTransaction.type)

        total_income = Decimal("0")
        total_expenses = Decimal("0")
        for tx_type, total in self._session.exec(query).all():
            if tx_type == TransactionType.INCOME.value:
                total_income += total
            else:
                total_expenses += total
        return total_income, total_expenses

    def recent(self, user_id: UUID, limit: int = 5) -> list[DomainTransaction]:
        items = self._session.exec(
            select(ORMTransaction)
            .where(
                ORMTransaction.user_id == user_id,
                ORMTransaction.is_deleted == False,
            )
            .order_by(ORMTransaction.created_at.desc())
            .limit(limit)
        ).all()
        return [self._to_domain(t) for t in items]
