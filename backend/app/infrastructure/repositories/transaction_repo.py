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

from sqlmodel import Session, select, func

from app.core.domain.transaction import Transaction as DomainTransaction
from app.core.exceptions import NotFoundError
from app.core.ports.transaction_repo import TransactionRepository
from app.models.transaction import Transaction as ORMTransaction


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
            is_deleted=orm.is_deleted,
            wallet_id=orm.wallet_id,
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
            is_deleted=domain.is_deleted,
            wallet_id=domain.wallet_id,
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
        self._session.commit()
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
        self._session.commit()

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
        self._session.add(orm)
        self._session.commit()
        self._session.refresh(orm)
        return self._to_domain(orm)

    def sum_by_wallet(self, wallet_id: UUID, user_id: UUID) -> Decimal:
        result = self._session.exec(
            select(func.sum(ORMTransaction.amount_base)).where(
                ORMTransaction.wallet_id == wallet_id,
                ORMTransaction.user_id == user_id,
                ORMTransaction.is_deleted == False,
            )
        ).one()
        return result or Decimal("0")

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

    def monthly_spending_by_category(
        self,
        user_id: UUID,
        year: int,
        month: int,
        exclude_categories: list[str] | None = None,
    ) -> dict[str, Decimal]:
        from datetime import date as _date
        month_start = _date(year, month, 1)
        month_end = _date(year + 1, 1, 1) if month == 12 else _date(year, month + 1, 1)

        query = select(
            ORMTransaction.category,
            func.sum(ORMTransaction.amount_base).label("total"),
        ).where(
            ORMTransaction.user_id == user_id,
            ORMTransaction.is_deleted == False,
            ORMTransaction.transaction_date >= month_start,
            ORMTransaction.transaction_date < month_end,
        )
        if exclude_categories:
            query = query.where(ORMTransaction.category.notin_(exclude_categories))
        query = query.group_by(ORMTransaction.category)

        result: dict[str, Decimal] = {}
        for cat, total in self._session.exec(query).all():
            result[cat] = total
        return result

    def cash_flow(
        self,
        user_id: UUID,
        from_date: date,
        to_date: date,
        income_categories: list[str],
        savings_categories: list[str],
    ) -> list[dict]:
        exclude = set(income_categories) | set(savings_categories)
        rows = self._session.exec(
            select(
                ORMTransaction.transaction_date,
                ORMTransaction.category,
                func.sum(ORMTransaction.amount_base).label("total"),
            )
            .where(
                ORMTransaction.user_id == user_id,
                ORMTransaction.is_deleted == False,
                ORMTransaction.transaction_date >= from_date,
                ORMTransaction.transaction_date <= to_date,
                ORMTransaction.category.notin_(list(exclude)) if exclude else True,
            )
            .group_by(ORMTransaction.transaction_date, ORMTransaction.category)
            .order_by(ORMTransaction.transaction_date)
        ).all()

        daily: dict[date, dict] = {}
        for tx_date, category, total in rows:
            if tx_date not in daily:
                daily[tx_date] = {"date": str(tx_date), "income": 0.0, "expenses": 0.0}
            if category in income_categories:
                daily[tx_date]["income"] += float(total)
            else:
                daily[tx_date]["expenses"] += float(total)

        result = sorted(daily.values(), key=lambda x: x["date"])
        running = 0.0
        for day in result:
            running += day["income"] - day["expenses"]
            day["balance"] = round(running, 2)
            day["income"] = round(day["income"], 2)
            day["expenses"] = round(day["expenses"], 2)
        return result

    def net_worth_trend(
        self,
        user_id: UUID,
        income_categories: list[str],
        expense_categories: list[str],
    ) -> list[dict]:
        rows = self._session.exec(
            select(
                func.strftime("%Y-%m", ORMTransaction.transaction_date).label("month"),
                ORMTransaction.category,
                func.sum(ORMTransaction.amount_base).label("total"),
            )
            .where(
                ORMTransaction.user_id == user_id,
                ORMTransaction.is_deleted == False,
            )
            .group_by(
                func.strftime("%Y-%m", ORMTransaction.transaction_date),
                ORMTransaction.category,
            )
            .order_by(func.strftime("%Y-%m", ORMTransaction.transaction_date))
        ).all()

        monthly: dict[str, float] = {}
        for month, category, total in rows:
            delta = float(total) if category in income_categories else -float(total)
            monthly[month] = monthly.get(month, 0.0) + delta

        cumulative = 0.0
        result = []
        for month in sorted(monthly):
            cumulative += monthly[month]
            result.append({"month": month, "net_worth": round(cumulative, 2)})
        return result

    def monthly_totals_by_type(
        self,
        user_id: UUID,
        year: int,
        month: int,
        type_map: dict[str, str],
        savings_categories: list[str],
    ) -> tuple[Decimal, Decimal]:
        from datetime import date as _date
        month_start = _date(year, month, 1)
        month_end = _date(year + 1, 1, 1) if month == 12 else _date(year, month + 1, 1)

        exclude = set(savings_categories)
        rows = self._session.exec(
            select(
                ORMTransaction.category,
                func.sum(ORMTransaction.amount_base).label("total"),
            )
            .where(
                ORMTransaction.user_id == user_id,
                ORMTransaction.is_deleted == False,
                ORMTransaction.transaction_date >= month_start,
                ORMTransaction.transaction_date < month_end,
                ORMTransaction.category.notin_(list(exclude)) if exclude else True,
            )
            .group_by(ORMTransaction.category)
        ).all()

        total_income = Decimal("0")
        total_expenses = Decimal("0")
        for cat, total in rows:
            if type_map.get(cat) == "income":
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
