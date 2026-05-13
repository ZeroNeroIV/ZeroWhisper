"""
Transaction router — CRUD endpoints with dual-currency support.
"""
from datetime import date as Date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionRead, PaginatedTransactions
from app.services import transactions as tx_service

router = APIRouter()


@router.get("", response_model=PaginatedTransactions)
def list_transactions(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    currency: Optional[str] = None,
    date_from: Optional[Date] = None,
    date_to: Optional[Date] = None,
    source: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Return a paginated, filtered list of the current user's transactions."""
    return tx_service.list_transactions(
        session=session,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        category=category,
        currency=currency,
        date_from=date_from,
        date_to=date_to,
        source=source,
    )


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    body: TransactionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new transaction. Computes amount_base in JOD automatically."""
    tx = tx_service.create_transaction(
        session=session,
        user_id=current_user.id,
        data=body,
        source="manual",
    )
    return tx_service._to_read(tx)


@router.get("/{tx_id}", response_model=TransactionRead)
def get_transaction(
    tx_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single transaction by ID."""
    tx = tx_service.get_transaction(session=session, tx_id=tx_id, user_id=current_user.id)
    return tx_service._to_read(tx)


@router.put("/{tx_id}", response_model=TransactionRead)
def update_transaction(
    tx_id: UUID,
    body: TransactionUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a transaction. Recomputes amount_base if amount or currency changes."""
    tx = tx_service.update_transaction(
        session=session,
        tx_id=tx_id,
        user_id=current_user.id,
        data=body,
    )
    return tx_service._to_read(tx)


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    tx_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a transaction (sets is_deleted=True)."""
    tx_service.delete_transaction(session=session, tx_id=tx_id, user_id=current_user.id)
