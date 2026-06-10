"""
SQLModel-backed ExchangeRateRepository implementation.
Translates between core/domain ExchangeRate objects and the SQLModel ORM.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session, select, desc

from app.core.domain.transaction import ExchangeRate as DomainRate
from app.core.ports.exchange_rate_repo import ExchangeRateRepository
from app.models.transaction import ExchangeRate as ORMRate


class SQLModelExchangeRateRepository(ExchangeRateRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    def set_rate(self, rate: Decimal, for_date: date, source: str = "manual") -> DomainRate:
        orm = ORMRate(date=for_date, jod_per_usd=rate, source=source)
        self._session.add(orm)
        self._session.flush()
        self._session.refresh(orm)
        return DomainRate(date=orm.date, jod_per_usd=orm.jod_per_usd, source=orm.source)

    def get_rate(self, for_date: date) -> DomainRate | None:
        result = self._session.exec(
            select(ORMRate)
            .where(ORMRate.date <= for_date)
            .order_by(ORMRate.date.desc())
            .limit(1)
        ).first()
        if result is None:
            return None
        return DomainRate(date=result.date, jod_per_usd=result.jod_per_usd, source=result.source)

    def get_current(self) -> DomainRate | None:
        result = self._session.exec(
            select(ORMRate).order_by(desc(ORMRate.date)).limit(1)
        ).first()
        if result is None:
            return None
        return DomainRate(date=result.date, jod_per_usd=result.jod_per_usd, source=result.source)

    def get_history(self, limit: int = 30) -> list[DomainRate]:
        results = self._session.exec(
            select(ORMRate).order_by(desc(ORMRate.date)).limit(limit)
        ).all()
        return [
            DomainRate(date=r.date, jod_per_usd=r.jod_per_usd, source=r.source)
            for r in results
        ]
