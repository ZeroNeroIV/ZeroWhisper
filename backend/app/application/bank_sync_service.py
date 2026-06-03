from __future__ import annotations

import json
import logging
from datetime import date, datetime
from uuid import UUID

from app.application.transaction_service import TransactionService
from app.core.ports.category_repo import CategoryRepository
from app.infrastructure.bank_connectors import get_connector, BankTransaction

logger = logging.getLogger(__name__)

# Keywords for basic category inference from bank transaction descriptions.
_INCOME_KEYWORDS = frozenset({"salary", "income", "deposit", "transfer in"})
_HOUSING_KEYWORDS = frozenset({"rent", "mortgage"})
_UTILITIES_KEYWORDS = frozenset({"electricity", "water", "internet", "phone", "gas"})
_FOOD_KEYWORDS = frozenset({"grocery", "supermarket", "food", "restaurant", "coffee", "cafe"})
_TRANSPORT_KEYWORDS = frozenset({"gasoline", "fuel", "petrol", "parking", "taxi", "uber"})


def _infer_category(description: str) -> str:
    desc_lower = description.lower()
    if any(w in desc_lower for w in _INCOME_KEYWORDS):
        return "Income"
    if any(w in desc_lower for w in _HOUSING_KEYWORDS):
        return "Housing"
    if any(w in desc_lower for w in _UTILITIES_KEYWORDS):
        return "Utilities"
    if any(w in desc_lower for w in _FOOD_KEYWORDS):
        return "Food"
    if any(w in desc_lower for w in _TRANSPORT_KEYWORDS):
        return "Transport"
    return "Other"


class BankSyncResult:
    imported: int
    skipped: int
    total: int

    def __init__(self, imported: int, skipped: int, total: int) -> None:
        self.imported = imported
        self.skipped = skipped
        self.total = total


class BankConnectionReader:
    """Reads bank connection data from a dict (decoupled from ORM)."""

    def __init__(self, data: dict) -> None:
        self._data = data

    @property
    def id(self) -> int:
        return self._data["id"]

    @property
    def user_id(self) -> UUID:
        return self._data["user_id"]

    @property
    def bank_name(self) -> str:
        return self._data["bank_name"]

    @property
    def auth_type(self) -> str:
        return self._data["auth_type"]

    @property
    def credentials(self) -> dict:
        raw = self._data.get("credentials", "{}")
        return json.loads(raw) if isinstance(raw, str) else raw

    @property
    def last_sync_at(self) -> datetime | None:
        return self._data.get("last_sync_at")


class BankSyncService:

    def __init__(
        self,
        tx_service: TransactionService,
        cat_repo: CategoryRepository,
    ) -> None:
        self._tx_service = tx_service
        self._cat_repo = cat_repo

    def _exists(self, user_id: UUID, btx: BankTransaction) -> bool:
        existing, _ = self._tx_service.list(
            user_id=user_id,
            page=1,
            page_size=1,
            date_from=btx.transaction_date,
            date_to=btx.transaction_date,
        )
        for tx in existing:
            if tx.description == btx.description:
                return True
        return False

    async def sync_connection(
        self,
        connection: BankConnectionReader,
    ) -> BankSyncResult:
        connector = get_connector(connection.auth_type)
        from_date = connection.last_sync_at.date() if connection.last_sync_at else None

        bank_txs = await connector.fetch_transactions(connection.credentials, from_date=from_date)

        imported = 0
        skipped = 0

        for btx in bank_txs:
            try:
                category = _infer_category(btx.description)

                existing, _ = self._tx_service.list(
                    user_id=connection.user_id,
                    page=1,
                    page_size=1,
                    date_from=btx.transaction_date,
                    date_to=btx.transaction_date,
                )
                dup = any(
                    t.description == btx.description and t.amount_original == btx.amount
                    for t in existing
                )
                if dup:
                    skipped += 1
                    continue

                self._tx_service.create(
                    user_id=connection.user_id,
                    amount_original=btx.amount,
                    currency_original=btx.currency,
                    category=category,
                    transaction_date=btx.transaction_date,
                    description=btx.description,
                    source=f"bank:{connection.bank_name}",
                )
                imported += 1
            except Exception as exc:
                logger.warning("Skipping bank tx %s: %s", btx.external_id, exc)
                skipped += 1

        return BankSyncResult(imported=imported, skipped=skipped, total=len(bank_txs))
