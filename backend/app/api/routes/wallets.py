from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import ContainerDep, SessionDep, UserDep
from app.application.transaction_service import TransactionService
from app.application.wallet_service import WalletService
from app.core.domain.user import User
from app.core.domain.wallet import WalletType
from app.schemas.transaction import TransactionRead, tx_to_read

router = APIRouter(prefix="/api/wallets", tags=["wallets"])


class CreateWalletRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    type: str = Field(default="cash", pattern=r"^(cash|digital|savings|credit|other)$")
    currency: str = Field(default="JOD", pattern=r"^(JOD|USD)$")
    initial_balance: Decimal = Field(default=Decimal("0"))
    icon: Optional[str] = None


class UpdateWalletRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    type: Optional[str] = Field(None, pattern=r"^(cash|digital|savings|credit|other)$")
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


@router.get("", response_model=list[WalletRead])
def list_wallets(
    container: ContainerDep,
    session: SessionDep,
    user: UserDep,
    include_inactive: bool = False,
):
    svc: WalletService = container.wallet_service(session)
    return [_wallet_to_read(w) for w in svc.list_wallets(user.id, include_inactive=include_inactive)]


@router.post("", status_code=201, response_model=WalletRead)
def create_wallet(
    container: ContainerDep,
    session: SessionDep,
    body: CreateWalletRequest,
    user: UserDep,
):
    svc: WalletService = container.wallet_service(session)
    w = svc.create(
        user.id, body.name, type=WalletType(body.type), currency=body.currency,
        initial_balance=body.initial_balance, icon=body.icon,
    )
    return _wallet_to_read(w)


@router.post("/transfer", status_code=201, response_model=TransferRead)
def transfer(
    container: ContainerDep,
    session: SessionDep,
    body: TransferRequest,
    user: UserDep,
):
    tx_svc: TransactionService = container.transaction_service(session)
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
    container: ContainerDep,
    session: SessionDep,
    wallet_id: UUID,
    user: UserDep,
):
    svc: WalletService = container.wallet_service(session)
    w = svc.get_wallet(wallet_id, user.id)
    if w is None:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return _wallet_to_read(w)


@router.patch("/{wallet_id}", response_model=WalletRead)
def update_wallet(
    container: ContainerDep,
    session: SessionDep,
    wallet_id: UUID,
    body: UpdateWalletRequest,
    user: UserDep,
):
    svc: WalletService = container.wallet_service(session)
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


@router.delete("/{wallet_id}", status_code=204)
def delete_wallet(
    container: ContainerDep,
    session: SessionDep,
    wallet_id: UUID,
    user: UserDep,
):
    svc: WalletService = container.wallet_service(session)
    ok = svc.delete(wallet_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Wallet not found")
