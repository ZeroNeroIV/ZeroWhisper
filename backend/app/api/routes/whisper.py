from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.deps import ContainerDep, SessionDep, UserDep
from app.application.whisper_service import WhisperService

router = APIRouter(prefix="/api/whisper", tags=["whisper"])


class ParseRequest(BaseModel):
    message: str


class ConfirmRequest(BaseModel):
    proposal_id: str
    overrides: dict | None = None


class RejectRequest(BaseModel):
    proposal_id: str


@router.post("/parse")
async def parse(
    container: ContainerDep,
    session: SessionDep,
    body: ParseRequest,
    user: UserDep,
):
    service: WhisperService = container.whisper_service(session)
    return await service.parse_message(user.id, body.message)


@router.post("/confirm", status_code=status.HTTP_201_CREATED)
def confirm(
    container: ContainerDep,
    session: SessionDep,
    body: ConfirmRequest,
    user: UserDep,
):
    service: WhisperService = container.whisper_service(session)
    tx = service.confirm(body.proposal_id, user.id, overrides=body.overrides)
    return {
        "id": str(tx.id),
        "amount_original": str(tx.amount_original),
        "currency_original": tx.currency_original,
        "amount_base": str(tx.amount_base),
        "category": tx.category,
        "type": tx.type.value,
        "description": tx.description,
        "transaction_date": tx.transaction_date.isoformat(),
        "source": tx.source,
        "wallet_id": str(tx.wallet_id) if tx.wallet_id else None,
        "transfer_id": str(tx.transfer_id) if tx.transfer_id else None,
    }


@router.post("/reject")
def reject(
    container: ContainerDep,
    session: SessionDep,
    body: RejectRequest,
    user: UserDep,
):
    service: WhisperService = container.whisper_service(session)
    if not service.reject(body.proposal_id, user.id):
        raise status.HTTP_404_NOT_FOUND
    return {"status": "rejected"}


@router.get("/ai-status")
def ai_status(
    container: ContainerDep,
    session: SessionDep,
    user: UserDep,
):
    service: WhisperService = container.whisper_service(session)
    provider = service.get_ai_provider()
    return {"provider": type(provider).__name__, "ready": True}
