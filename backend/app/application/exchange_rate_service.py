"""
Exchange rate use cases — rate lookup, management, and auto-fetch.
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from app.core.config import settings
from app.core.domain.transaction import ExchangeRate
from app.core.ports.exchange_rate_repo import ExchangeRateRepository
from app.infrastructure.exchange_rate_api import FrankfurterClient

logger = logging.getLogger(__name__)


class ExchangeRateService:

    def __init__(
        self,
        repo: ExchangeRateRepository,
        api_client: FrankfurterClient | None = None,
    ) -> None:
        self._repo = repo
        self._api_client = api_client or FrankfurterClient()
        self._auto_fetch: bool = settings.auto_fetch_exchange_rate

    def get_rate(self, for_date: date) -> Decimal:
        existing = self._repo.get_rate(for_date)
        if existing is not None:
            return existing.jod_per_usd
        if self._auto_fetch:
            fetched = self._api_client.fetch_jod_per_usd(for_date)
            if fetched is not None:
                self._repo.set_rate(fetched, for_date, source="auto")
                return fetched
        return Decimal(str(settings.default_exchange_rate))

    def set_rate(self, rate: Decimal, for_date: date, source: str = "manual") -> ExchangeRate:
        return self._repo.set_rate(rate, for_date, source)

    def get_current(self) -> ExchangeRate | None:
        return self._repo.get_current()

    def get_history(self, limit: int = 30) -> list[ExchangeRate]:
        return self._repo.get_history(limit)

    def toggle_auto_fetch(self, enabled: bool) -> bool:
        self._auto_fetch = enabled
        return enabled
