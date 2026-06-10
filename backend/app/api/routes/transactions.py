"""Transaction API routes — thin HTTP glue for transaction CRUD."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.application.transaction_service import TransactionService
from app.core.domain.user import User
from app.schemas.transaction import (
    PaginatedTransactions,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
    tx_to_read,
)

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
    type: str | None = None,
):
    df = date.fromisoformat(date_from) if date_from else None
    dt = date.fromisoformat(date_to) if date_to else None
    wid = UUID(wallet_id) if wallet_id else None
    items, total = service.list(
        user.id, page, page_size, category, currency, df, dt, source, wid, type,
    )
    return PaginatedTransactions(
        items=[tx_to_read(tx) for tx in items],
        total=total, page=page, page_size=page_size,
        pages=max(1, -(-total // page_size)),
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TransactionRead)
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
    return tx_to_read(tx)


@router.get("/{tx_id}", response_model=TransactionRead)
def get_transaction(
    request: Request,
    tx_id: UUID,
    user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
):
    return tx_to_read(service.get(tx_id, user.id))


@router.put("/{tx_id}", response_model=TransactionRead)
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
    return tx_to_read(tx)


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    request: Request,
    tx_id: UUID,
    user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
):
    service.delete(tx_id, user.id)
