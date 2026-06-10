from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import ContainerDep, SessionDep, UserDep
from app.application.transaction_service import TransactionService
from app.schemas.transaction import (
    PaginatedTransactions,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
    tx_to_read,
)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("")
def list_transactions(
    container: ContainerDep,
    session: SessionDep,
    user: UserDep,
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
    import math
    service: TransactionService = container.transaction_service(session)
    items, total = service.list(
        user.id, page, page_size, category, currency, df, dt, source, wid, type,
    )
    return PaginatedTransactions(
        items=[tx_to_read(tx) for tx in items],
        total=total, page=page, page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TransactionRead)
def create_transaction(
    container: ContainerDep,
    session: SessionDep,
    body: TransactionCreate,
    user: UserDep,
):
    service: TransactionService = container.transaction_service(session)
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
    container: ContainerDep,
    session: SessionDep,
    tx_id: UUID,
    user: UserDep,
):
    service: TransactionService = container.transaction_service(session)
    return tx_to_read(service.get(tx_id, user.id))


@router.put("/{tx_id}", response_model=TransactionRead)
def update_transaction(
    container: ContainerDep,
    session: SessionDep,
    tx_id: UUID,
    body: TransactionUpdate,
    user: UserDep,
):
    service: TransactionService = container.transaction_service(session)
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
    container: ContainerDep,
    session: SessionDep,
    tx_id: UUID,
    user: UserDep,
):
    service: TransactionService = container.transaction_service(session)
    service.delete(tx_id, user.id)
