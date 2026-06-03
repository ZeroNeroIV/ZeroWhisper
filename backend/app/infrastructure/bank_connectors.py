"""
Pluggable bank connector interface.
Each connector knows how to authenticate and fetch transactions from a specific bank API.
"""
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
import logging

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BankTransaction(BaseModel):
    external_id: str
    amount: Decimal
    currency: str
    description: str
    transaction_date: date


class BaseBankConnector(ABC):
    @abstractmethod
    async def fetch_transactions(
        self,
        credentials: dict,
        from_date: date | None = None,
    ) -> list[BankTransaction]:
        ...


class ApiKeyConnector(BaseBankConnector):
    """
    Generic REST API connector with API key authentication.
    Credentials: { "api_url": "https://api.bank.com/transactions", "api_key": "..." }
    """

    async def fetch_transactions(
        self,
        credentials: dict,
        from_date: date | None = None,
    ) -> list[BankTransaction]:
        url = credentials.get("api_url", "")
        api_key = credentials.get("api_key", "")
        if not url or not api_key:
            logger.warning("ApiKeyConnector: missing api_url or api_key")
            return []

        params: dict = {}
        if from_date:
            params["from"] = from_date.isoformat()

        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}

        try:
            response = httpx.get(url, params=params, headers=headers, timeout=15.0)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.warning("ApiKeyConnector fetch failed: %s", exc)
            return []

        return _parse_response(data)


class BasicAuthConnector(BaseBankConnector):
    """
    REST API connector with username/password authentication.
    Credentials: { "api_url": "...", "username": "...", "password": "..." }
    """

    async def fetch_transactions(
        self,
        credentials: dict,
        from_date: date | None = None,
    ) -> list[BankTransaction]:
        url = credentials.get("api_url", "")
        username = credentials.get("username", "")
        password = credentials.get("password", "")
        if not url or not username or not password:
            logger.warning("BasicAuthConnector: missing credentials")
            return []

        params: dict = {}
        if from_date:
            params["from"] = from_date.isoformat()

        try:
            response = httpx.get(
                url, params=params, auth=(username, password), timeout=15.0
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.warning("BasicAuthConnector fetch failed: %s", exc)
            return []

        return _parse_response(data)


def _parse_response(data: dict | list) -> list[BankTransaction]:
    """
    Attempt to parse bank API response into a list of BankTransaction.
    Tries common response shapes:
      - {"transactions": [...]}
      - {"data": [...]}
      - [...] (direct list)
    """
    items: list = []
    if isinstance(data, dict):
        items = data.get("transactions") or data.get("data") or data.get("items") or []
    elif isinstance(data, list):
        items = data
    else:
        return []

    results: list[BankTransaction] = []
    for item in items:
        try:
            raw_date = item.get("date") or item.get("transaction_date") or item.get("Date")
            parsed_date = (
                date.fromisoformat(raw_date[:10]) if isinstance(raw_date, str) else date.today()
            )
            results.append(
                BankTransaction(
                    external_id=str(item.get("id", "") or item.get("transaction_id", "")),
                    amount=Decimal(str(item.get("amount", 0))),
                    currency=str(item.get("currency", "JOD")),
                    description=str(item.get("description", "") or item.get("narrative", "")),
                    transaction_date=parsed_date,
                )
            )
        except Exception as exc:
            logger.warning("Skipping malformed bank transaction: %s", exc)
            continue

    return results


def get_connector(auth_type: str) -> BaseBankConnector:
    if auth_type == "basic":
        return BasicAuthConnector()
    return ApiKeyConnector()
