"""Whisper API routes — natural language and voice transaction entry."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.application.whisper_service import WhisperService
from app.core.domain.user import User
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/api/whisper", tags=["whisper"])


class ParseRequest(BaseModel):
    message: str


class ConfirmRequest(BaseModel):
    proposal_id: str


class RejectRequest(BaseModel):
    proposal_id: str


def _get_service(request: Request, session: Session = Depends(get_session)) -> WhisperService:
    return request.app.state.container.whisper_service(session)


@router.post("/parse")
async def parse(
    body: ParseRequest,
    request: Request,
    user: User = Depends(get_current_user),
    service: WhisperService = Depends(_get_service),
):
    result = await service.parse_message(user.id, body.message)
    return result


@router.post("/confirm", status_code=status.HTTP_201_CREATED)
def confirm(
    body: ConfirmRequest,
    request: Request,
    user: User = Depends(get_current_user),
    service: WhisperService = Depends(_get_service),
):
    try:
        tx = service.confirm(body.proposal_id, user.id)
    except NotFoundError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=e.detail)

    return {
        "id": str(tx.id),
        "amount_original": str(tx.amount_original),
        "currency_original": tx.currency_original,
        "amount_base": str(tx.amount_base),
        "category": tx.category,
        "description": tx.description,
        "transaction_date": tx.transaction_date.isoformat(),
        "source": tx.source,
    }


@router.post("/reject")
def reject(
    body: RejectRequest,
    request: Request,
    user: User = Depends(get_current_user),
    service: WhisperService = Depends(_get_service),
):
    if not service.reject(body.proposal_id, user.id):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Proposal not found")
    return {"status": "rejected"}


@router.get("/ai-status")
def ai_status(
    request: Request,
    user: User = Depends(get_current_user),
    service: WhisperService = Depends(_get_service),
):
    provider = service.get_ai_provider()
    return {"provider": type(provider).__name__, "ready": True}
