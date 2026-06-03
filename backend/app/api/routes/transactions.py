"""Transaction API routes — thin HTTP glue for transaction CRUD."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session
from pydantic import BaseModel

from app.api.deps import get_current_user, get_session
from app.application.transaction_service import TransactionService
from app.core.domain.user import User
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionRead, PaginatedTransactions

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def _get_service(request: Request, session: Session = Depends(get_session)) -> TransactionService:
    return request.app.state.container.transaction_service(session)


@router.get("")
def list_transactions(
    request: Request,
    user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    currency: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    source: str | None = None,
    wallet_id: str | None = None,
):
    from datetime import date
    from uuid import UUID
    df = date.fromisoformat(date_from) if date_from else None
    dt = date.fromisoformat(date_to) if date_to else None
    wid = UUID(wallet_id) if wallet_id else None
    items, total = service.list(user.id, page, page_size, category, currency, df, dt, source, wid)
    return PaginatedTransactions(
        items=[TransactionRead(
            id=tx.id, user_id=tx.user_id, amount_original=tx.amount_original,
            currency_original=tx.currency_original, amount_base=tx.amount_base,
            exchange_rate=tx.exchange_rate, category=tx.category,
            description=tx.description, transaction_date=tx.transaction_date,
            source=tx.source, wallet_id=tx.wallet_id,
            created_at=tx.created_at.isoformat(),
        ) for tx in items],
        total=total, page=page, page_size=page_size,
        pages=max(1, -(-total // page_size)),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_transaction(
    request: Request,
    body: TransactionCreate,
    user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
):
    tx = service.create(
        user_id=user.id,
        amount_original=body.amount_original,
        currency_original=body.currency_original,
        category=body.category,
        transaction_date=body.transaction_date,
        description=body.description,
        wallet_id=body.wallet_id,
    )
    return TransactionRead(
        id=tx.id, user_id=tx.user_id, amount_original=tx.amount_original,
        currency_original=tx.currency_original, amount_base=tx.amount_base,
        exchange_rate=tx.exchange_rate, category=tx.category,
        description=tx.description, transaction_date=tx.transaction_date,
        source=tx.source, wallet_id=tx.wallet_id, created_at=tx.created_at.isoformat(),
    )


@router.get("/{tx_id}")
def get_transaction(
    request: Request,
    tx_id: UUID,
    user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
):
    tx = service.get(tx_id, user.id)
    return TransactionRead(
        id=tx.id, user_id=tx.user_id, amount_original=tx.amount_original,
        currency_original=tx.currency_original, amount_base=tx.amount_base,
        exchange_rate=tx.exchange_rate, category=tx.category,
        description=tx.description, transaction_date=tx.transaction_date,
        source=tx.source, wallet_id=tx.wallet_id,
        created_at=tx.created_at.isoformat(),
    )


@router.put("/{tx_id}")
def update_transaction(
    request: Request,
    tx_id: UUID,
    body: TransactionUpdate,
    user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
):
    tx = service.update(
        tx_id=tx_id, user_id=user.id,
        amount_original=body.amount_original,
        currency_original=body.currency_original,
        category=body.category,
        description=body.description,
        transaction_date=body.transaction_date,
        wallet_id=body.wallet_id,
    )
    return TransactionRead(
        id=tx.id, user_id=tx.user_id, amount_original=tx.amount_original,
        currency_original=tx.currency_original, amount_base=tx.amount_base,
        exchange_rate=tx.exchange_rate, category=tx.category,
        description=tx.description, transaction_date=tx.transaction_date,
        source=tx.source, wallet_id=tx.wallet_id,
        created_at=tx.created_at.isoformat(),
    )


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    request: Request,
    tx_id: UUID,
    user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
):
    service.delete(tx_id, user.id)
