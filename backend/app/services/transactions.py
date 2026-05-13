from decimal import Decimal
from datetime import date
from uuid import UUID
from typing import Optional

from sqlmodel import Session, select, func

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate, PaginatedTransactions
from app.services.exchange_rate import get_rate
from app.exceptions import not_found


def create_transaction(
    session: Session,
    user_id: UUID,
    data: TransactionCreate,
    source: str = "manual",
) -> Transaction:
    """
    Create a transaction. Computes amount_base in JOD using the exchange rate
    for transaction_date. If currency is JOD, rate is 1.0 and amount_base == amount_original.
    """
    if data.currency_original == "JOD":
        rate = Decimal("1.0")
        amount_base = data.amount_original
    else:
        rate = get_rate(session, data.transaction_date)
        amount_base = (data.amount_original * rate).quantize(Decimal("0.000001"))

    tx = Transaction(
        user_id=user_id,
        amount_original=data.amount_original,
        currency_original=data.currency_original,
        amount_base=amount_base,
        exchange_rate=rate,
        category=data.category,
        description=data.description,
        transaction_date=data.transaction_date,
        source=source,
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


def get_transaction(session: Session, tx_id: UUID, user_id: UUID) -> Transaction:
    tx = session.exec(
        select(Transaction).where(
            Transaction.id == tx_id,
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
        )
    ).first()
    if not tx:
        raise not_found("Transaction not found")
    return tx


def list_transactions(
    session: Session,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    currency: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    source: Optional[str] = None,
) -> PaginatedTransactions:
    """Paginated, filterable list of non-deleted transactions for a user."""
    query = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.is_deleted == False,
    )
    if category:
        query = query.where(Transaction.category == category)
    if currency:
        query = query.where(Transaction.currency_original == currency)
    if date_from:
        query = query.where(Transaction.transaction_date >= date_from)
    if date_to:
        query = query.where(Transaction.transaction_date <= date_to)
    if source:
        query = query.where(Transaction.source == source)

    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()

    items = session.exec(
        query.order_by(Transaction.transaction_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return PaginatedTransactions(
        items=[_to_read(tx) for tx in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, -(-total // page_size)),  # ceiling division
    )


def update_transaction(
    session: Session, tx_id: UUID, user_id: UUID, data: TransactionUpdate
) -> Transaction:
    tx = get_transaction(session, tx_id, user_id)
    update_data = data.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(tx, field, value)

    # Recompute base amount if currency or amount changed
    if "amount_original" in update_data or "currency_original" in update_data:
        if tx.currency_original == "JOD":
            tx.exchange_rate = Decimal("1.0")
            tx.amount_base = tx.amount_original
        else:
            rate = get_rate(session, tx.transaction_date)
            tx.exchange_rate = rate
            tx.amount_base = (tx.amount_original * rate).quantize(Decimal("0.000001"))

    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


def delete_transaction(session: Session, tx_id: UUID, user_id: UUID) -> None:
    tx = get_transaction(session, tx_id, user_id)
    tx.is_deleted = True
    session.add(tx)
    session.commit()


def _to_read(tx: Transaction) -> dict:
    return {
        "id": tx.id,
        "user_id": tx.user_id,
        "amount_original": tx.amount_original,
        "currency_original": tx.currency_original,
        "amount_base": tx.amount_base,
        "exchange_rate": tx.exchange_rate,
        "category": tx.category,
        "description": tx.description,
        "transaction_date": tx.transaction_date,
        "source": tx.source,
        "created_at": tx.created_at.isoformat(),
    }
