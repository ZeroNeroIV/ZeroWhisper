"""API key routes — CRUD for API keys (MCP authentication)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.application.api_key_service import ApiKeyService
from app.core.domain.user import User

router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])


class CreateKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)


class ApiKeyRead(BaseModel):
    id: int
    prefix: str
    name: str
    last_used_at: Optional[datetime]
    created_at: datetime


class CreateKeyResponse(BaseModel):
    key: str
    id: int
    prefix: str
    name: str
    warning: str = "Store this key securely — it cannot be shown again"


def _get_svc(request: Request, session: Session = Depends(get_session)) -> ApiKeyService:
    return request.app.state.container.api_key_service(session)


@router.get("", response_model=list[ApiKeyRead])
def get_api_keys(
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(_get_svc),
) -> list[ApiKeyRead]:
    keys = service.list_keys(current_user.id)
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
    service: ApiKeyService = Depends(_get_svc),
) -> CreateKeyResponse:
    key_data, raw_key = service.create(current_user.id, body.name)
    return CreateKeyResponse(
        key=raw_key,
        id=key_data.id,
        prefix=key_data.prefix,
        name=key_data.name,
    )


@router.delete("/{key_id}", status_code=204)
def delete_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(_get_svc),
) -> None:
    revoked = service.revoke(key_id, current_user.id)
    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")
