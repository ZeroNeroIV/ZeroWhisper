"""
Exchange rate router — CRUD endpoints for managing JOD/USD rates.
"""
from datetime import date as Date
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.config import settings
from app.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.services import exchange_rate as rate_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class SetRateRequest(BaseModel):
    rate: Decimal
    date: Date


class AutoFetchToggle(BaseModel):
    enabled: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/current")
def get_current(
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_user),
):
    """
    Return the current (most recent) exchange rate.
    If auto-fetch is enabled, attempt to pull today's rate first.
    Falls back to the configured default when no stored rate exists.
    """
    rate_service.maybe_auto_fetch(session)
    row = rate_service.get_current_rate(session)
    if row is None:
        return {"rate": settings.default_exchange_rate, "source": "default"}
    return {"rate": row.jod_per_usd, "date": row.date, "source": row.source}


@router.get("/history")
def get_history(
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_user),
):
    """Return the 30 most recent exchange rate records, newest first."""
    rows = rate_service.get_history(session, limit=30)
    return rows


@router.post("")
def create_rate(
    body: SetRateRequest,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_user),
):
    """Manually set (or overwrite) the exchange rate for a given date."""
    row = rate_service.set_rate(session, body.rate, body.date, source="manual")
    return row


@router.put("/auto-fetch")
def toggle_auto_fetch(
    body: AutoFetchToggle,
    _user: User = Depends(get_current_user),
):
    """
    Enable or disable automatic exchange rate fetching at runtime.
    The override is stored in a module-level variable (not persisted across restarts).
    """
    rate_service._auto_fetch_override = body.enabled
    return {"auto_fetch_enabled": body.enabled}
