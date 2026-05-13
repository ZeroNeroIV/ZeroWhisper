"""
Exchange rate service — storage, retrieval, and optional auto-fetch from Frankfurter API.
"""
import logging
from datetime import date, datetime
from decimal import Decimal

import httpx
from sqlmodel import Session, select

from app.config import settings
from app.models.transaction import ExchangeRate

logger = logging.getLogger(__name__)

# Module-level override for auto-fetch toggle (set via PUT /api/exchange-rates/auto-fetch).
# None means "use settings.auto_fetch_exchange_rate"; True/False overrides it at runtime.
_auto_fetch_override: bool | None = None


def set_rate(session: Session, rate: Decimal, for_date: date, source: str = "manual") -> ExchangeRate:
    """
    Store an exchange rate for the given date.
    Overwrites the existing row for that date if one already exists.
    """
    statement = select(ExchangeRate).where(ExchangeRate.date == for_date)
    existing = session.exec(statement).first()

    if existing:
        existing.jod_per_usd = rate
        existing.source = source
        existing.created_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    new_rate = ExchangeRate(date=for_date, jod_per_usd=rate, source=source)
    session.add(new_rate)
    session.commit()
    session.refresh(new_rate)
    return new_rate


def get_rate(session: Session, for_date: date) -> Decimal:
    """
    Return the JOD/USD exchange rate effective on or before `for_date`.
    Falls back to settings.default_exchange_rate if no rate is found.
    """
    statement = (
        select(ExchangeRate)
        .where(ExchangeRate.date <= for_date)
        .order_by(ExchangeRate.date.desc())
        .limit(1)
    )
    row = session.exec(statement).first()
    if row is None:
        return Decimal(str(settings.default_exchange_rate))
    return row.jod_per_usd


def get_current_rate(session: Session) -> ExchangeRate | None:
    """Return the most recent ExchangeRate row, or None if none exist."""
    statement = select(ExchangeRate).order_by(ExchangeRate.date.desc()).limit(1)
    return session.exec(statement).first()


def get_history(session: Session, limit: int = 30) -> list[ExchangeRate]:
    """Return the last `limit` exchange rates, newest first."""
    statement = select(ExchangeRate).order_by(ExchangeRate.date.desc()).limit(limit)
    return list(session.exec(statement).all())


def maybe_auto_fetch(session: Session) -> ExchangeRate | None:
    """
    If auto-fetch is enabled and no rate exists for today, fetch from Frankfurter API
    and store it.  Returns the new ExchangeRate on success, None otherwise.
    """
    auto_fetch_enabled = (
        _auto_fetch_override if _auto_fetch_override is not None
        else settings.auto_fetch_exchange_rate
    )
    if not auto_fetch_enabled:
        return None

    today = date.today()

    # Skip fetch if a rate for today already exists.
    existing = session.exec(
        select(ExchangeRate).where(ExchangeRate.date == today)
    ).first()
    if existing:
        return None

    try:
        response = httpx.get(
            "https://api.frankfurter.app/latest",
            params={"from": "USD", "to": "JOD"},
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()
        jod_rate = Decimal(str(data["rates"]["JOD"]))
    except Exception as exc:
        logger.warning("Auto-fetch exchange rate failed: %s", exc)
        return None

    return set_rate(session, jod_rate, today, source="api")
