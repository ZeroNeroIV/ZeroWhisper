"""Exchange rate API routes — thin HTTP glue for rate CRUD."""
from __future__ import annotations

from datetime import date as Date
from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.application.exchange_rate_service import ExchangeRateService
from app.core.config import settings
from app.core.domain.user import User

router = APIRouter(prefix="/api/exchange-rates", tags=["exchange-rates"])


class SetRateRequest(BaseModel):
    rate: Decimal
    date: Date


class AutoFetchToggle(BaseModel):
    enabled: bool


def _get_service(request: Request, session: Session = Depends(get_session)) -> ExchangeRateService:
    return request.app.state.container.exchange_rate_service(session)


@router.get("/current")
def get_current(
    request: Request,
    _user: User = Depends(get_current_user),
    service: ExchangeRateService = Depends(_get_service),
):
    row = service.get_current()
    if row is None:
        return {"rate": settings.default_exchange_rate, "source": "default"}
    return {"rate": row.jod_per_usd, "date": row.date, "source": row.source}


@router.get("/history")
def get_history(
    request: Request,
    _user: User = Depends(get_current_user),
    service: ExchangeRateService = Depends(_get_service),
):
    return service.get_history(limit=30)


@router.post("")
def create_rate(
    request: Request,
    body: SetRateRequest,
    _user: User = Depends(get_current_user),
    service: ExchangeRateService = Depends(_get_service),
):
    row = service.set_rate(body.rate, body.date, source="manual")
    return row


@router.put("/auto-fetch")
def toggle_auto_fetch(
    request: Request,
    body: AutoFetchToggle,
    _user: User = Depends(get_current_user),
    service: ExchangeRateService = Depends(_get_service),
):
    service.toggle_auto_fetch(body.enabled)
    return {"auto_fetch_enabled": body.enabled}


class FxSettingsResponse(BaseModel):
    fx_api_url: str
    fx_api_key: str


class FxSettingsUpdate(BaseModel):
    fx_api_url: str | None = None
    fx_api_key: str | None = None


@router.get("/settings")
def get_fx_settings(
    _user: User = Depends(get_current_user),
):
    from app.infrastructure import ai_settings
    key = ai_settings.get("fx_api_key", "")
    masked = key[:8] + "\u2022" * min(8, max(0, len(key) - 8)) if key else ""
    return {
        "fx_api_url": ai_settings.get("fx_api_url", "https://api.frankfurter.app/latest"),
        "fx_api_key": masked,
    }


@router.put("/settings")
def update_fx_settings(
    body: FxSettingsUpdate,
    _user: User = Depends(get_current_user),
):
    from app.infrastructure import ai_settings
    patch = {}
    if body.fx_api_url is not None:
        patch["fx_api_url"] = body.fx_api_url
    if body.fx_api_key is not None:
        patch["fx_api_key"] = body.fx_api_key
    if patch:
        ai_settings.update(patch)
    return get_fx_settings(_user=_user)
