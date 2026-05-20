from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import Session
from typing import Optional

from app.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.agent import AgentRequest, WhisperResponse
from app.services import openai_service, whisper_service
from app.services.openai_service import transcribe_health_check
from app.services.transactions import _to_read

router = APIRouter()


class ConfirmRequest(BaseModel):
    proposal_id: str
    overrides: Optional[dict] = None


class RejectRequest(BaseModel):
    proposal_id: str


@router.post("/parse", response_model=WhisperResponse)
async def parse(
    body: AgentRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await whisper_service.parse_message(session, str(current_user.id), body.message)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/confirm", status_code=status.HTTP_201_CREATED)
def confirm(
    body: ConfirmRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        tx = whisper_service.confirm_proposal(
            session, body.proposal_id, str(current_user.id), body.overrides
        )
        return _to_read(tx)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found or expired")


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Transcribe an audio recording using OpenAI Whisper and return the transcript."""
    if not transcribe_health_check():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OpenAI API key not configured for transcription")
    data = await audio.read()
    filename = audio.filename or "recording.webm"
    try:
        text = await openai_service.transcribe_audio(data, filename)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    return {"text": text}


@router.get("/ai-status")
def ai_status(current_user: User = Depends(get_current_user)):
    """Return current AI provider configuration and readiness."""
    return openai_service.ai_status()


@router.post("/reject")
def reject(
    body: RejectRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    whisper_service.reject_proposal(body.proposal_id, str(current_user.id))
    return {"status": "rejected"}
