"""
Analytics use cases — cash flow, Sankey, heatmap, net worth trend.

Every analytics function follows the same pattern:
1. Get category type map and savings categories from the repo
2. Compute using TransactionRepository aggregation methods
3. Return presentation-ready dicts

This replaces the old analytics_service.py which duplicated category lookups
and month-end calculation in every function.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from uuid import UUID

from app.core.ports.transaction_repo import TransactionRepository
from app.core.ports.category_repo import CategoryRepository
from app.core.domain.category import CategoryType


def _month_end(year: int, month: int) -> dt.date:
    """Return the first day of the next month (for exclusive range queries).

    This eliminates the if/else for December that was duplicated across
    3 files in the old code.
    """
    if month == 12:
        return dt.date(year + 1, 1, 1)
    return dt.date(year, month + 1, 1)


class AnalyticsService:

    def __init__(
        self,
        tx_repo: TransactionRepository,
        cat_repo: CategoryRepository,
    ) -> None:
        self._tx_repo = tx_repo
        self._cat_repo = cat_repo

    def get_cash_flow(self, user_id: UUID, from_date: dt.date, to_date: dt.date) -> list[dict]:
        type_map = self._cat_repo.get_type_map(user_id)
        income_cats = [cat for cat, t in type_map.items() if t == "income"]
        savings_cats = [cat for cat, t in type_map.items() if t == "savings"]
        return self._tx_repo.cash_flow(user_id, from_date, to_date, income_cats, savings_cats)

    def get_sankey(self, user_id: UUID, year: int, month: int) -> dict:
        type_map = self._cat_repo.get_type_map(user_id)
        savings_cats = [cat for cat, t in type_map.items() if t == "savings"]

        month_start = dt.date(year, month, 1)
        month_end = _month_end(year, month)

        spending = self._tx_repo.monthly_spending_by_category(
            user_id, year, month,
            exclude_categories=savings_cats,
        )

        total_income = Decimal("0")
        spending_cats: list[tuple[str, Decimal]] = []
        for cat, total in spending.items():
            if type_map.get(cat) == "income":
                total_income += total
            else:
                spending_cats.append((cat, total))

        nodes = [{"name": "Income"}] + [{"name": cat} for cat, _ in spending_cats]
        links = [
            {"source": 0, "target": i + 1, "value": round(float(val), 2)}
            for i, (_, val) in enumerate(spending_cats)
        ]
        return {
            "nodes": nodes,
            "links": links,
            "total_income": round(float(total_income), 2),
        }

    def get_heatmap(self, user_id: UUID, year: int, month: int) -> list[dict]:
        type_map = self._cat_repo.get_type_map(user_id)
        exclude_cats = [cat for cat, t in type_map.items() if t in ("income", "savings")]

        month_start = dt.date(year, month, 1)
        month_end = _month_end(year, month)

        # We need day-level breakdown; use the repo's monthly method
        spending = self._tx_repo.monthly_spending_by_category(
            user_id, year, month,
            exclude_categories=exclude_cats,
        )
        # Heatmap requires per-day per-category breakdown
        # For now, return category-level totals (improvement for Phase 3)
        return [
            {"category": cat, "amount": round(float(total), 2)}
            for cat, total in sorted(spending.items(), key=lambda x: -float(x[1]))
            if type_map.get(cat) != "income"
        ]

    def get_net_worth_trend(self, user_id: UUID) -> list[dict]:
        type_map = self._cat_repo.get_type_map(user_id)
        income_cats = [cat for cat, t in type_map.items() if t == "income"]
        expense_cats = [cat for cat, t in type_map.items() if t == "expense"]

        return self._tx_repo.net_worth_trend(user_id, income_cats, expense_cats)

    def get_dashboard_summary(self, user_id: UUID) -> dict:
        type_map = self._cat_repo.get_type_map(user_id)
        savings_cats = [cat for cat, t in type_map.items() if t == "savings"]
        income_cats = [cat for cat, t in type_map.items() if t == "income"]
        expense_cats = [cat for cat, t in type_map.items() if t == "expense"]

        now = dt.date.today()

        # Lifetime balance
        total_income = self._tx_repo.sum_by_categories(user_id, income_cats)
        total_expenses = self._tx_repo.sum_by_categories(user_id, expense_cats)
        total_savings = self._tx_repo.sum_by_categories(user_id, savings_cats)

        # Monthly totals
        month_income, month_expenses = self._tx_repo.monthly_totals_by_type(
            user_id, now.year, now.month, type_map, savings_cats,
        )

        recent = self._tx_repo.recent(user_id, limit=5)

        return {
            "balance": str(total_income - total_expenses),
            "this_month_spending": str(month_expenses),
            "this_month_income": str(month_income),
            "total_savings": str(total_savings),
            "recent_transactions": [
                {
                    "id": str(t.id),
                    "amount_original": str(t.amount_original),
                    "currency_original": t.currency_original,
                    "amount_base": str(t.amount_base),
                    "category": t.category,
                    "description": t.description,
                    "transaction_date": t.transaction_date.isoformat(),
                    "source": t.source,
                }
                for t in recent
            ],
        }
