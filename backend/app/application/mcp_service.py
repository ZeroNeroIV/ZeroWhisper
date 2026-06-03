"""
MCP use cases — provides financial data to AI agents via the Model Context Protocol.

All responses exclude PII (no descriptions) to prevent leakage to third-party AI.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from app.core.ports.transaction_repo import TransactionRepository
from app.core.ports.category_repo import CategoryRepository


class MCPService:

    def __init__(self, tx_repo: TransactionRepository, cat_repo: CategoryRepository) -> None:
        self._tx_repo = tx_repo
        self._cat_repo = cat_repo

    def get_balance(self, user_id: UUID) -> dict:
        type_map = self._cat_repo.get_type_map(user_id)
        income_cats = [cat for cat, t in type_map.items() if t == "income"]
        expense_cats = [cat for cat, t in type_map.items() if t == "expense"]

        income = self._tx_repo.sum_by_categories(user_id, income_cats)
        expenses = self._tx_repo.sum_by_categories(user_id, expense_cats)

        return {
            "balance_jod": str(income - expenses),
            "currency": "JOD",
        }

    def get_recent_transactions(self, user_id: UUID, limit: int = 10) -> list[dict]:
        transactions = self._tx_repo.recent(user_id, limit=limit)
        return [
            {
                "date": tx.transaction_date.isoformat(),
                "category": tx.category,
                "amount_jod": str(tx.amount_base),
                "currency_original": tx.currency_original,
                "source": tx.source,
            }
            for tx in transactions
        ]

    def get_spending_by_category(self, user_id: UUID, month: int, year: int) -> list[dict]:
        type_map = self._cat_repo.get_type_map(user_id)
        income_cats = [cat for cat, t in type_map.items() if t == "income"]
        savings_cats = [cat for cat, t in type_map.items() if t == "savings"]
        exclude_cats = income_cats + savings_cats

        spending = self._tx_repo.monthly_spending_by_category(
            user_id, year, month,
            exclude_categories=exclude_cats,
        )

        grand_total = sum(spending.values(), Decimal("0"))
        result = []
        for cat, total in spending.items():
            pct = round(float(total / grand_total) * 100, 2) if grand_total > 0 else 0.0
            result.append({
                "category": cat,
                "total_jod": str(total),
                "pct_of_total": pct,
            })

        result.sort(key=lambda x: Decimal(x["total_jod"]), reverse=True)
        return result

    def get_net_worth(self, user_id: UUID) -> dict:
        type_map = self._cat_repo.get_type_map(user_id)
        income_cats = [cat for cat, t in type_map.items() if t == "income"]
        expense_cats = [cat for cat, t in type_map.items() if t == "expense"]
        savings_cats = [cat for cat, t in type_map.items() if t == "savings"]

        total_income = self._tx_repo.sum_by_categories(user_id, income_cats)
        total_expenses = self._tx_repo.sum_by_categories(user_id, expense_cats)
        total_savings = self._tx_repo.sum_by_categories(user_id, savings_cats)

        return {
            "total_income_jod": str(total_income),
            "total_expenses_jod": str(total_expenses),
            "total_savings_jod": str(total_savings),
            "net_worth_jod": str(total_income - total_expenses),
        }
