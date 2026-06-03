"""
ExchangeRateRepository port — abstract persistence contract for exchange rates.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from app.core.domain.transaction import ExchangeRate


class ExchangeRateRepository(ABC):

    @abstractmethod
    def set_rate(self, rate: Decimal, for_date: date, source: str = "manual") -> ExchangeRate:
        ...

    @abstractmethod
    def get_rate(self, for_date: date) -> ExchangeRate | None:
        ...

    @abstractmethod
    def get_current(self) -> ExchangeRate | None:
        ...

    @abstractmethod
    def get_history(self, limit: int = 30) -> list[ExchangeRate]:
        ...
