"""
Analytics use cases — cash flow, Sankey, heatmap, net worth trend.

Direction (income vs expense) is classified by the transaction's own `type`
column — the single source of truth — never by looking the category name up
in a type map. Category types are only used for the orthogonal "savings"
dimension (savings are excluded from spending views but still belong to the
user's balance).

All aggregation stays in Decimal; rounding to float happens once, here, at
the presentation edge.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from uuid import UUID

from app.core.ports.transaction_repo import TransactionRepository
from app.core.ports.category_repo import CategoryRepository


def _round(value: Decimal) -> float:
    return float(round(value, 2))


class AnalyticsService:

    def __init__(
        self,
        tx_repo: TransactionRepository,
        cat_repo: CategoryRepository,
    ) -> None:
        self._tx_repo = tx_repo
        self._cat_repo = cat_repo

    def _savings_categories(self, user_id: UUID) -> list[str]:
        type_map = self._cat_repo.get_type_map(user_id)
        return [cat for cat, t in type_map.items() if t == "savings"]

    def get_cash_flow(self, user_id: UUID, from_date: dt.date, to_date: dt.date) -> list[dict]:
        savings = self._savings_categories(user_id)
        rows = self._tx_repo.daily_flow(user_id, from_date, to_date, exclude_categories=savings)

        result: list[dict] = []
        running = Decimal("0")
        for day, income, expenses in rows:
            running += income - expenses
            result.append({
                "date": str(day),
                "income": _round(income),
                "expenses": _round(expenses),
                "balance": _round(running),
            })
        return result

    def get_sankey(self, user_id: UUID, year: int, month: int) -> dict:
        savings = self._savings_categories(user_id)
        spending = self._tx_repo.monthly_spending_by_category(
            user_id, year, month,
            exclude_categories=savings,
            types=["expense"],
        )
        total_income, _ = self._tx_repo.totals_by_type(user_id, year, month)
        if not spending and total_income == 0:
            return {"nodes": [], "links": [], "total_income": 0.0}

        spending_cats = sorted(spending.items(), key=lambda kv: kv[1], reverse=True)
        nodes = [{"name": "Income"}] + [{"name": cat} for cat, _ in spending_cats]
        links = [
            {"source": 0, "target": i + 1, "value": _round(val)}
            for i, (_, val) in enumerate(spending_cats)
        ]
        return {
            "nodes": nodes,
            "links": links,
            "total_income": _round(total_income),
        }

    def get_heatmap(self, user_id: UUID, year: int, month: int) -> list[dict]:
        savings = self._savings_categories(user_id)
        rows = self._tx_repo.daily_spending_by_category(
            user_id, year, month,
            exclude_categories=savings,
        )
        return [
            {"day": day, "category": category, "amount": _round(total)}
            for day, category, total in rows
        ]

    def get_net_worth_trend(self, user_id: UUID) -> list[dict]:
        cumulative = Decimal("0")
        result = []
        for month, net in self._tx_repo.monthly_net(user_id):
            cumulative += net
            result.append({"month": month, "net_worth": _round(cumulative)})
        return result

    def get_dashboard_summary(self, user_id: UUID) -> dict:
        savings_cats = self._savings_categories(user_id)
        now = dt.date.today()

        total_income, total_expenses = self._tx_repo.totals_by_type(
            user_id, exclude_categories=savings_cats,
        )
        total_savings = self._tx_repo.sum_by_categories(user_id, savings_cats)
        month_income, month_expenses = self._tx_repo.totals_by_type(
            user_id, now.year, now.month, exclude_categories=savings_cats,
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
