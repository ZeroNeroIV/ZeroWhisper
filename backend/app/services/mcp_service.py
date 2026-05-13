from decimal import Decimal
from datetime import date
from uuid import UUID

from sqlmodel import Session, select, func

from app.models.transaction import Transaction


def get_balance(session: Session, user_id: UUID) -> dict:
    """
    Sum all non-deleted transactions for the user.
    Income category is additive; all others are subtractive.
    Returns {"balance_jod": str, "currency": "JOD"}
    """
    income_sum = session.exec(
        select(func.sum(Transaction.amount_base)).where(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
            Transaction.category == "Income",
        )
    ).one()

    expense_sum = session.exec(
        select(func.sum(Transaction.amount_base)).where(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
            Transaction.category != "Income",
        )
    ).one()

    income = income_sum or Decimal("0")
    expenses = expense_sum or Decimal("0")
    balance = income - expenses

    return {
        "balance_jod": str(balance),
        "currency": "JOD",
    }


def get_recent_transactions(session: Session, user_id: UUID, limit: int = 10) -> list[dict]:
    """
    Return the last `limit` non-deleted transactions.
    Each dict: {date, category, amount_jod, currency_original, source}
    NO description field — prevents PII leakage.
    """
    transactions = session.exec(
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
        )
        .order_by(Transaction.transaction_date.desc())
        .limit(limit)
    ).all()

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


def get_spending_by_category(
    session: Session, user_id: UUID, month: int, year: int
) -> list[dict]:
    """
    Group non-deleted transactions for the given month/year by category.
    Returns [{category, total_jod, count, pct_of_total}] sorted by total_jod desc.
    Excludes "Income" category from the spending totals.
    pct_of_total: percentage of this category's total vs all categories (0-100, rounded 2dp).
    """
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    transactions = session.exec(
        select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
            Transaction.category != "Income",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date,
        )
    ).all()

    # Python-side grouping
    category_totals: dict[str, Decimal] = {}
    category_counts: dict[str, int] = {}

    for tx in transactions:
        cat = tx.category
        category_totals[cat] = category_totals.get(cat, Decimal("0")) + tx.amount_base
        category_counts[cat] = category_counts.get(cat, 0) + 1

    grand_total = sum(category_totals.values(), Decimal("0"))

    result = []
    for cat, total in category_totals.items():
        pct = (
            round(float(total / grand_total) * 100, 2)
            if grand_total > Decimal("0")
            else 0.0
        )
        result.append(
            {
                "category": cat,
                "total_jod": str(total),
                "count": category_counts[cat],
                "pct_of_total": pct,
            }
        )

    result.sort(key=lambda x: Decimal(x["total_jod"]), reverse=True)
    return result


def get_net_worth(session: Session, user_id: UUID) -> dict:
    """
    Compute lifetime totals.
    total_income: sum of amount_base where category == "Income" and not deleted
    total_expenses: sum of amount_base where category != "Income" and not deleted
    net_worth: total_income - total_expenses
    Returns {"total_income_jod", "total_expenses_jod", "net_worth_jod"}
    """
    income_sum = session.exec(
        select(func.sum(Transaction.amount_base)).where(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
            Transaction.category == "Income",
        )
    ).one()

    expense_sum = session.exec(
        select(func.sum(Transaction.amount_base)).where(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
            Transaction.category != "Income",
        )
    ).one()

    total_income = income_sum or Decimal("0")
    total_expenses = expense_sum or Decimal("0")
    net_worth = total_income - total_expenses

    return {
        "total_income_jod": str(total_income),
        "total_expenses_jod": str(total_expenses),
        "net_worth_jod": str(net_worth),
    }
