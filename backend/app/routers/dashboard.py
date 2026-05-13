from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
import datetime as dt
from decimal import Decimal

from app.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import Transaction

router = APIRouter()

@router.get("/summary")
def get_summary(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    now = dt.datetime.utcnow()
    month_start = dt.date(now.year, now.month, 1)

    base_q = (
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .where(Transaction.is_deleted == False)
    )

    # Total balance = sum of all income - sum of all expenses (in JOD)
    income_total = session.exec(select(func.sum(Transaction.amount_base)).where(
        Transaction.user_id == current_user.id,
        Transaction.is_deleted == False,
        Transaction.category == "Income",
    )).one() or Decimal(0)

    expense_total = session.exec(select(func.sum(Transaction.amount_base)).where(
        Transaction.user_id == current_user.id,
        Transaction.is_deleted == False,
        Transaction.category != "Income",
    )).one() or Decimal(0)

    month_income = session.exec(select(func.sum(Transaction.amount_base)).where(
        Transaction.user_id == current_user.id,
        Transaction.is_deleted == False,
        Transaction.category == "Income",
        Transaction.transaction_date >= month_start,
    )).one() or Decimal(0)

    month_expense = session.exec(select(func.sum(Transaction.amount_base)).where(
        Transaction.user_id == current_user.id,
        Transaction.is_deleted == False,
        Transaction.category != "Income",
        Transaction.transaction_date >= month_start,
    )).one() or Decimal(0)

    recent = session.exec(
        base_q.order_by(Transaction.transaction_date.desc()).limit(5)
    ).all()

    return {
        "balance_jod": float(income_total - expense_total),
        "month_spending_jod": float(month_expense),
        "month_income_jod": float(month_income),
        "recent_transactions": [
            {
                "id": str(tx.id),
                "category": tx.category,
                "description": tx.description,
                "amount_original": float(tx.amount_original),
                "currency_original": tx.currency_original,
                "transaction_date": str(tx.transaction_date),
            }
            for tx in recent
        ],
    }
