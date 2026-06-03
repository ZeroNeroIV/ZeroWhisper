"""
Transaction use cases — orchestrates transaction CRUD with exchange rate conversion.

This layer owns the business rules:
- Dual-currency conversion (JOD base computation)
- Category validation before save
- Soft-delete semantics
- Exchange rate lookup and override

It depends only on port interfaces, not on infrastructure.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from app.core.domain.transaction import Transaction as DomainTransaction
from app.core.exceptions import NotFoundError, ValidationError
from app.core.ports.transaction_repo import TransactionRepository
from app.core.ports.category_repo import CategoryRepository
from app.application.exchange_rate_service import ExchangeRateService


class TransactionService:

    def __init__(
        self,
        tx_repo: TransactionRepository,
        cat_repo: CategoryRepository,
        rate_service: ExchangeRateService,
    ) -> None:
        self._tx_repo = tx_repo
        self._cat_repo = cat_repo
        self._rate_service = rate_service

    def _validate_category(self, user_id: UUID, name: str) -> None:
        cat = self._cat_repo.find_by_name(user_id, name)
        if not cat:
            raise ValidationError(f"Invalid category '{name}'")

    def create(
        self,
        user_id: UUID,
        amount_original: Decimal,
        currency_original: str,
        category: str,
        transaction_date: date,
        description: str | None = None,
        source: str = "manual",
        exchange_rate_override: Decimal | None = None,
        wallet_id: UUID | None = None,
    ) -> DomainTransaction:
        self._validate_category(user_id, category)

        if currency_original == "JOD":
            rate = Decimal("1.0")
            amount_base = amount_original
        else:
            rate = exchange_rate_override or self._rate_service.get_rate(transaction_date)
            amount_base = DomainTransaction.compute_base_amount(amount_original, currency_original, rate)

        tx = DomainTransaction(
            user_id=user_id,
            amount_original=amount_original,
            currency_original=currency_original,
            category=category,
            transaction_date=transaction_date,
            amount_base=amount_base,
            exchange_rate=rate,
            description=description,
            source=source,
            wallet_id=wallet_id,
        )
        return self._tx_repo.save(tx)

    def get(self, tx_id: UUID, user_id: UUID) -> DomainTransaction:
        tx = self._tx_repo.find_by_id(tx_id, user_id)
        if not tx:
            raise NotFoundError("Transaction", str(tx_id))
        return tx

    def list(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        currency: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        source: str | None = None,
        wallet_id: UUID | None = None,
    ) -> tuple[list[DomainTransaction], int]:
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        return self._tx_repo.find_by_user(
            user_id,
            page=page,
            page_size=page_size,
            category=category,
            currency=currency,
            date_from=date_from,
            date_to=date_to,
            source=source,
            wallet_id=wallet_id,
        )

    def update(
        self,
        tx_id: UUID,
        user_id: UUID,
        *,
        amount_original: Decimal | None = None,
        currency_original: str | None = None,
        category: str | None = None,
        description: str | None = None,
        transaction_date: date | None = None,
        wallet_id: UUID | None = None,
    ) -> DomainTransaction:
        tx = self.get(tx_id, user_id)
        if category is not None:
            self._validate_category(user_id, category)
            tx.category = category
        if description is not None:
            tx.description = description
        if transaction_date is not None:
            tx.transaction_date = transaction_date
        if amount_original is not None:
            tx.amount_original = amount_original
        if currency_original is not None:
            tx.currency_original = currency_original
        if wallet_id is not None:
            tx.wallet_id = wallet_id

        # Recompute base amount if currency or amount changed
        if amount_original is not None or currency_original is not None:
            if tx.currency_original == "JOD":
                tx.exchange_rate = Decimal("1.0")
                tx.amount_base = tx.amount_original
            else:
                rate = self._rate_service.get_rate(tx.transaction_date)
                tx.exchange_rate = rate
                tx.amount_base = DomainTransaction.compute_base_amount(
                    tx.amount_original, tx.currency_original, rate
                )

        return self._tx_repo.update(tx)

    def delete(self, tx_id: UUID, user_id: UUID) -> None:
        self.get(tx_id, user_id)  # ensure exists
        self._tx_repo.soft_delete(tx_id, user_id)
