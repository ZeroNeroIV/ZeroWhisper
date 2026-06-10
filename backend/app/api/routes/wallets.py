"""Wallet routes — CRUD, archiving, and inter-wallet transfers."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.application.transaction_service import TransactionService
from app.application.wallet_service import WalletService
from app.core.domain.user import User
from app.core.domain.wallet import WalletType
from app.schemas.transaction import TransactionRead, tx_to_read

router = APIRouter(prefix="/api/wallets", tags=["wallets"])

WalletTypeLiteral = Literal["cash", "digital", "savings", "credit", "other"]


class CreateWalletRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    type: WalletTypeLiteral = "cash"
    currency: str = Field(default="JOD", pattern=r"^(JOD|USD)$")
    initial_balance: Decimal = Field(default=Decimal("0"))
    icon: Optional[str] = None


class UpdateWalletRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    type: Optional[WalletTypeLiteral] = None
    currency: Optional[str] = Field(None, pattern=r"^(JOD|USD)$")
    initial_balance: Optional[Decimal] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class TransferRequest(BaseModel):
    from_wallet_id: UUID
    to_wallet_id: UUID
    amount_original: Decimal = Field(..., gt=0)
    currency_original: str = Field(default="JOD", pattern=r"^(JOD|USD)$")
    transaction_date: Optional[date] = None
    description: Optional[str] = None


class WalletRead(BaseModel):
    id: UUID
    name: str
    type: str
    currency: str
    balance: Decimal
    initial_balance: Decimal
    icon: Optional[str]
    is_active: bool
    created_at: str


class TransferRead(BaseModel):
    transfer_id: UUID
    out_leg: TransactionRead
    in_leg: TransactionRead


def _wallet_to_read(w) -> WalletRead:
    return WalletRead(
        id=w.id, name=w.name, type=w.type.value, currency=w.currency,
        balance=w.balance, initial_balance=w.initial_balance,
        icon=w.icon, is_active=w.is_active,
        created_at=w.created_at.isoformat(),
    )


def _get_svc(request: Request, session: Session = Depends(get_session)) -> WalletService:
    return request.app.state.container.wallet_service(session)


def _get_tx_svc(request: Request, session: Session = Depends(get_session)) -> TransactionService:
    return request.app.state.container.transaction_service(session)


@router.get("", response_model=list[WalletRead])
def list_wallets(
    include_inactive: bool = False,
    user: User = Depends(get_current_user),
    svc: WalletService = Depends(_get_svc),
):
    return [_wallet_to_read(w) for w in svc.list_wallets(user.id, include_inactive=include_inactive)]


@router.post("", status_code=201, response_model=WalletRead)
def create_wallet(
    body: CreateWalletRequest,
    user: User = Depends(get_current_user),
    svc: WalletService = Depends(_get_svc),
):
    w = svc.create(
        user.id, body.name, type=WalletType(body.type), currency=body.currency,
        initial_balance=body.initial_balance, icon=body.icon,
    )
    return _wallet_to_read(w)


@router.post("/transfer", status_code=201, response_model=TransferRead)
def transfer(
    body: TransferRequest,
    user: User = Depends(get_current_user),
    tx_svc: TransactionService = Depends(_get_tx_svc),
):
    out_leg, in_leg = tx_svc.transfer(
        user_id=user.id,
        from_wallet_id=body.from_wallet_id,
        to_wallet_id=body.to_wallet_id,
        amount_original=body.amount_original,
        currency_original=body.currency_original,
        transaction_date=body.transaction_date or date.today(),
        description=body.description,
    )
    return TransferRead(
        transfer_id=out_leg.transfer_id,
        out_leg=tx_to_read(out_leg),
        in_leg=tx_to_read(in_leg),
    )


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


@router.patch("/{wallet_id}", response_model=WalletRead)
def update_wallet(
    wallet_id: UUID,
    body: UpdateWalletRequest,
    user: User = Depends(get_current_user),
    svc: WalletService = Depends(_get_svc),
):
    w = svc.update(
        wallet_id, user.id,
        name=body.name,
        type=WalletType(body.type) if body.type else None,
        currency=body.currency,
        initial_balance=body.initial_balance,
        icon=body.icon,
        is_active=body.is_active,
    )
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
