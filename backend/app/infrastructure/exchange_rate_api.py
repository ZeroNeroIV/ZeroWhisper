"""
Frankfurter API client — fetches exchange rates from the public Frankfurter API.
This is an infrastructure concern isolated behind a simple interface.
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)


class FrankfurterClient:
    """HTTP client for Frankfurter exchange rate API."""

    def __init__(self, base_url: str = "https://api.frankfurter.dev") -> None:
        self._base_url = base_url.rstrip("/")

    def fetch_jod_per_usd(self, for_date: date) -> Decimal | None:
        """Fetch JOD per USD rate for the given date (synchronous)."""
        try:
            date_str = for_date.isoformat()
            resp = httpx.get(
                f"{self._base_url}/api/{date_str}?from=USD&to=JOD",
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return Decimal(str(data["rates"]["JOD"]))
        except Exception as exc:
            logger.warning("Exchange rate API fetch failed for %s: %s", for_date, exc)
            return None
