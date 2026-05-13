import datetime as dt
from decimal import Decimal
from sqlmodel import Session, select, func
from app.models.transaction import Transaction
from uuid import UUID


def get_cash_flow(session: Session, user_id: UUID, from_date: dt.date, to_date: dt.date) -> list[dict]:
    """Daily totals: income positive, expenses negative, running balance."""
    rows = session.exec(
        select(
            Transaction.transaction_date,
            Transaction.category,
            func.sum(Transaction.amount_base).label("total"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
            Transaction.transaction_date >= from_date,
            Transaction.transaction_date <= to_date,
        )
        .group_by(Transaction.transaction_date, Transaction.category)
        .order_by(Transaction.transaction_date)
    ).all()

    daily: dict[dt.date, dict] = {}
    for date, category, total in rows:
        if date not in daily:
            daily[date] = {"date": str(date), "income": 0.0, "expenses": 0.0}
        if category == "Income":
            daily[date]["income"] += float(total)
        else:
            daily[date]["expenses"] += float(total)

    result = sorted(daily.values(), key=lambda x: x["date"])
    running = 0.0
    for day in result:
        running += day["income"] - day["expenses"]
        day["balance"] = round(running, 2)
        day["income"] = round(day["income"], 2)
        day["expenses"] = round(day["expenses"], 2)
    return result


def get_sankey(session: Session, user_id: UUID, year: int, month: int) -> dict:
    """Category totals for Sankey: Income flows into spending categories."""
    month_start = dt.date(year, month, 1)
    if month == 12:
        month_end = dt.date(year + 1, 1, 1)
    else:
        month_end = dt.date(year, month + 1, 1)

    rows = session.exec(
        select(Transaction.category, func.sum(Transaction.amount_base).label("total"))
        .where(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date < month_end,
        )
        .group_by(Transaction.category)
    ).all()

    total_income = sum(float(t) for cat, t in rows if cat == "Income")
    spending = [(cat, float(t)) for cat, t in rows if cat != "Income"]

    nodes = ["Income"] + [cat for cat, _ in spending]
    links = [{"source": 0, "target": i + 1, "value": round(val, 2)} for i, (_, val) in enumerate(spending)]
    return {"nodes": [{"name": n} for n in nodes], "links": links, "total_income": round(total_income, 2)}


def get_heatmap(session: Session, user_id: UUID, year: int, month: int) -> list[dict]:
    """Spending by day+category for heatmap."""
    month_start = dt.date(year, month, 1)
    if month == 12:
        month_end = dt.date(year + 1, 1, 1)
    else:
        month_end = dt.date(year, month + 1, 1)

    rows = session.exec(
        select(
            Transaction.transaction_date,
            Transaction.category,
            func.sum(Transaction.amount_base).label("total"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date < month_end,
            Transaction.category != "Income",
        )
        .group_by(Transaction.transaction_date, Transaction.category)
    ).all()

    return [
        {"day": date.day, "category": cat, "amount": round(float(total), 2)}
        for date, cat, total in rows
    ]


def get_net_worth_trend(session: Session, user_id: UUID) -> list[dict]:
    """Monthly cumulative net worth."""
    rows = session.exec(
        select(
            func.strftime("%Y-%m", Transaction.transaction_date).label("month"),
            Transaction.category,
            func.sum(Transaction.amount_base).label("total"),
        )
        .where(Transaction.user_id == user_id, Transaction.is_deleted == False)
        .group_by(func.strftime("%Y-%m", Transaction.transaction_date), Transaction.category)
        .order_by(func.strftime("%Y-%m", Transaction.transaction_date))
    ).all()

    monthly: dict[str, float] = {}
    for month, category, total in rows:
        delta = float(total) if category == "Income" else -float(total)
        monthly[month] = monthly.get(month, 0.0) + delta

    cumulative = 0.0
    result = []
    for month in sorted(monthly):
        cumulative += monthly[month]
        result.append({"month": month, "net_worth": round(cumulative, 2)})
    return result
