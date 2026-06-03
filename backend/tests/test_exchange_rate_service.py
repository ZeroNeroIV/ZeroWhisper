from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.application.exchange_rate_service import ExchangeRateService
from app.core.ports.exchange_rate_repo import ExchangeRateRepository


@pytest.fixture
def repo() -> MagicMock:
    return MagicMock(spec=ExchangeRateRepository)


@pytest.fixture
def svc(repo: MagicMock) -> ExchangeRateService:
    return ExchangeRateService(repo)


class TestGetRate:
    def test_delegates_to_repo(self, svc: ExchangeRateService, repo: MagicMock) -> None:
        from app.core.domain.transaction import ExchangeRate
        repo.get_rate.return_value = ExchangeRate(date(2025, 6, 1), Decimal("0.710"))
        rate = svc.get_rate(date(2025, 6, 1))
        assert rate == Decimal("0.710")
        repo.get_rate.assert_called_once_with(date(2025, 6, 1))


class TestSetRate:
    def test_delegates_to_repo(self, svc: ExchangeRateService, repo: MagicMock) -> None:
        svc.set_rate(Decimal("0.720"), date(2025, 6, 1), source="manual")
        repo.set_rate.assert_called_once_with(Decimal("0.720"), date(2025, 6, 1), "manual")


class TestGetCurrent:
    def test_delegates_to_repo(self, svc: ExchangeRateService, repo: MagicMock) -> None:
        svc.get_current()
        repo.get_current.assert_called_once()


class TestGetHistory:
    def test_delegates_to_repo(self, svc: ExchangeRateService, repo: MagicMock) -> None:
        svc.get_history(limit=10)
        repo.get_history.assert_called_once_with(10)


class TestToggleAutoFetch:
    def test_enables(self, svc: ExchangeRateService, _repo: MagicMock) -> None:
        result = svc.toggle_auto_fetch(True)
        assert result is True

    def test_disables(self, svc: ExchangeRateService, _repo: MagicMock) -> None:
        result = svc.toggle_auto_fetch(False)
        assert result is False
