from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.services.api_key_service import create_api_key, list_keys, revoke_key

router = APIRouter(tags=["api-keys"])


class CreateKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)


class ApiKeyRead(BaseModel):
    id: int
    prefix: str          # masked display: "zwp_abc1****"
    name: str
    last_used_at: Optional[datetime]
    created_at: datetime


class CreateKeyResponse(BaseModel):
    key: str             # full raw key — shown ONCE
    id: int
    prefix: str
    name: str
    warning: str = "Store this key securely — it cannot be shown again"


@router.get("", response_model=list[ApiKeyRead])
def get_api_keys(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[ApiKeyRead]:
    keys = list_keys(session, current_user.id)
    return [
        ApiKeyRead(
            id=k.id,
            prefix=k.prefix,
            name=k.name,
            last_used_at=k.last_used_at,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.post("", response_model=CreateKeyResponse, status_code=201)
def create_key(
    body: CreateKeyRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> CreateKeyResponse:
    key, raw_key = create_api_key(session, current_user.id, body.name)
    return CreateKeyResponse(
        key=raw_key,
        id=key.id,
        prefix=key.prefix,
        name=key.name,
    )


@router.delete("/{key_id}", status_code=204)
def delete_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> None:
    revoked = revoke_key(session, key_id, current_user.id)
    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")
