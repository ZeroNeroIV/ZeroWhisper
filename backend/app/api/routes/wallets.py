"""Wallet routes — CRUD for wallets with balance recalculation."""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.application.wallet_service import WalletService
from app.core.domain.user import User

router = APIRouter(prefix="/api/wallets", tags=["wallets"])


class CreateWalletRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    currency: str = Field(default="JOD", pattern=r"^(JOD|USD)$")
    initial_balance: Decimal = Field(default=Decimal("0"))


class WalletRead(BaseModel):
    id: UUID
    name: str
    currency: str
    balance: Decimal
    is_active: bool
    created_at: str


def _wallet_to_read(w) -> WalletRead:
    return WalletRead(
        id=w.id, name=w.name, currency=w.currency,
        balance=w.balance, is_active=w.is_active,
        created_at=w.created_at.isoformat(),
    )


def _get_svc(request: Request, session: Session = Depends(get_session)) -> WalletService:
    return request.app.state.container.wallet_service(session)


@router.get("", response_model=list[WalletRead])
def list_wallets(
    user: User = Depends(get_current_user),
    svc: WalletService = Depends(_get_svc),
):
    return [_wallet_to_read(w) for w in svc.list_wallets(user.id)]


@router.post("", status_code=201, response_model=WalletRead)
def create_wallet(
    body: CreateWalletRequest,
    user: User = Depends(get_current_user),
    svc: WalletService = Depends(_get_svc),
):
    w = svc.create(user.id, body.name, body.currency, body.initial_balance)
    return _wallet_to_read(w)


@router.get("/{wallet_id}", response_model=WalletRead)
def get_wallet(
    wallet_id: UUID,
    user: User = Depends(get_current_user),
    svc: WalletService = Depends(_get_svc),
):
    w = svc.get_wallet(wallet_id, user.id)
    if w is None:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return _wallet_to_read(w)


@router.post("/{wallet_id}/recalculate", response_model=WalletRead)
def recalculate_wallet(
    wallet_id: UUID,
    user: User = Depends(get_current_user),
    svc: WalletService = Depends(_get_svc),
):
    w = svc.get_wallet(wallet_id, user.id)
    if w is None:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return _wallet_to_read(w)


@router.delete("/{wallet_id}", status_code=204)
def delete_wallet(
    wallet_id: UUID,
    user: User = Depends(get_current_user),
    svc: WalletService = Depends(_get_svc),
):
    ok = svc.delete(wallet_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Wallet not found")
