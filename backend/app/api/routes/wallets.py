"""Wallet routes — CRUD for wallets."""
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


def _get_svc(request: Request, session: Session = Depends(get_session)) -> WalletService:
    return request.app.state.container.wallet_service(session)


@router.get("")
def list_wallets(
    user: User = Depends(get_current_user),
    svc: WalletService = Depends(_get_svc),
):
    return svc.list_wallets(user.id)


@router.post("", status_code=201)
def create_wallet(
    body: CreateWalletRequest,
    user: User = Depends(get_current_user),
    svc: WalletService = Depends(_get_svc),
):
    wallet = svc.create(user.id, body.name, body.currency, body.initial_balance)
    return wallet


@router.get("/{wallet_id}")
def get_wallet(
    wallet_id: UUID,
    user: User = Depends(get_current_user),
    svc: WalletService = Depends(_get_svc),
):
    wallet = svc.get_wallet(wallet_id, user.id)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet


@router.delete("/{wallet_id}", status_code=204)
def delete_wallet(
    wallet_id: UUID,
    user: User = Depends(get_current_user),
    svc: WalletService = Depends(_get_svc),
):
    ok = svc.delete(wallet_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Wallet not found")
