"""
Transaction use cases — orchestrates transaction CRUD with exchange rate conversion.

This layer owns the business rules:
- Dual-currency conversion (JOD base computation)
- Category validation before save
- Transaction direction (income adds to a wallet, expense subtracts)
- Inter-wallet transfers as a linked pair of transactions
- Soft-delete semantics
- Exchange rate lookup and override

It depends only on port interfaces, not on infrastructure.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from app.core.domain.category import Category, CategoryType
from app.core.domain.transaction import (
    SOURCE_MANUAL,
    Transaction as DomainTransaction,
    TransactionType,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.ports.category_repo import CategoryRepository
from app.core.ports.transaction_repo import TransactionRepository
from app.core.ports.wallet_repo import WalletRepository
from app.application.exchange_rate_service import ExchangeRateService


class TransactionService:

    def __init__(
        self,
        tx_repo: TransactionRepository,
        cat_repo: CategoryRepository,
        rate_service: ExchangeRateService,
        wallet_repo: WalletRepository | None = None,
    ) -> None:
        self._tx_repo = tx_repo
        self._cat_repo = cat_repo
        self._rate_service = rate_service
        self._wallet_repo = wallet_repo

    def _validate_category(self, user_id: UUID, name: str) -> Category:
        cat = self._cat_repo.find_by_name(user_id, name)
        if not cat:
            raise ValidationError(f"Invalid category '{name}'")
        return cat

    def _validate_wallet(self, user_id: UUID, wallet_id: UUID):
        if self._wallet_repo is None:
            return None
        wallet = self._wallet_repo.get(wallet_id, user_id)
        if not wallet:
            raise ValidationError(f"Invalid wallet '{wallet_id}'")
        if not wallet.is_active:
            raise ValidationError(f"Wallet '{wallet.name}' is archived")
        return wallet

    @staticmethod
    def _derive_type(category: Category) -> TransactionType:
        """Income categories add to a wallet; everything else spends from it."""
        if category.type == CategoryType.INCOME:
            return TransactionType.INCOME
        return TransactionType.EXPENSE

    def _resolve_rate(
        self,
        currency: str,
        tx_date: date,
        override: Decimal | None = None,
    ) -> tuple[Decimal, Decimal | None]:
        if currency == "JOD":
            return Decimal("1.0"), None
        rate = override or self._rate_service.get_rate(tx_date)
        return rate, rate

    def create(
        self,
        user_id: UUID,
        amount_original: Decimal,
        currency_original: str,
        category: str,
        transaction_date: date,
        description: str | None = None,
        source: str = SOURCE_MANUAL,
        exchange_rate_override: Decimal | None = None,
        wallet_id: UUID | None = None,
        type: TransactionType | None = None,
    ) -> DomainTransaction:
        cat = self._validate_category(user_id, category)
        if cat.type == CategoryType.TRANSFER:
            raise ValidationError("Use the transfer endpoint to move money between wallets")
        if wallet_id is not None:
            self._validate_wallet(user_id, wallet_id)

        if type in (TransactionType.TRANSFER_IN, TransactionType.TRANSFER_OUT):
            raise ValidationError("Transfer legs can only be created via transfer()")

        rate, _ = self._resolve_rate(currency_original, transaction_date, exchange_rate_override)
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
            type=type or self._derive_type(cat),
            wallet_id=wallet_id,
        )
        return self._tx_repo.save(tx)

    def transfer(
        self,
        user_id: UUID,
        from_wallet_id: UUID,
        to_wallet_id: UUID,
        amount_original: Decimal,
        currency_original: str,
        transaction_date: date,
        description: str | None = None,
        source: str = SOURCE_MANUAL,
    ) -> tuple[DomainTransaction, DomainTransaction]:
        """Move money between two of the user's wallets.

        Creates a linked pair of transactions (out-leg and in-leg) sharing a
        transfer_id, categorized under the reserved Transfer category so the
        movement never shows up as income or spending in analytics.
        """
        if self._wallet_repo is None:
            raise ValidationError("Wallet support is not configured")
        if from_wallet_id == to_wallet_id:
            raise ValidationError("Source and destination wallets must differ")
        if amount_original <= 0:
            raise ValidationError("Transfer amount must be positive")

        source_wallet = self._validate_wallet(user_id, from_wallet_id)
        dest_wallet = self._validate_wallet(user_id, to_wallet_id)

        transfer_cat = self._cat_repo.get_or_create_transfer_category(user_id)
        rate, _ = self._resolve_rate(currency_original, transaction_date)
        amount_base = DomainTransaction.compute_base_amount(amount_original, currency_original, rate)

        transfer_id = uuid4()
        description = description or f"{source_wallet.name} → {dest_wallet.name}"

        common = dict(
            user_id=user_id,
            amount_original=amount_original,
            currency_original=currency_original,
            category=transfer_cat.name,
            transaction_date=transaction_date,
            amount_base=amount_base,
            exchange_rate=rate,
            description=description,
            source=source,
            transfer_id=transfer_id,
        )
        out_leg = self._tx_repo.save(DomainTransaction(
            **common, type=TransactionType.TRANSFER_OUT, wallet_id=from_wallet_id,
        ))
        in_leg = self._tx_repo.save(DomainTransaction(
            **common, type=TransactionType.TRANSFER_IN, wallet_id=to_wallet_id,
        ))
        return out_leg, in_leg

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
        type: str | None = None,
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
            type=type,
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
        if tx.is_transfer and (category is not None or wallet_id is not None):
            raise ValidationError(
                "Transfer legs cannot change category or wallet — delete the transfer and create a new one"
            )
        if category is not None:
            cat = self._validate_category(user_id, category)
            if cat.type == CategoryType.TRANSFER:
                raise ValidationError("Cannot recategorize a transaction as a transfer")
            tx.category = category
            tx.type = self._derive_type(cat)
        if description is not None:
            tx.description = description
        if transaction_date is not None:
            tx.transaction_date = transaction_date
        if amount_original is not None:
            tx.amount_original = amount_original
        if currency_original is not None:
            tx.currency_original = currency_original
        if wallet_id is not None:
            self._validate_wallet(user_id, wallet_id)
            tx.wallet_id = wallet_id

        # Recompute base amount if currency or amount changed
        if amount_original is not None or currency_original is not None:
            rate, _ = self._resolve_rate(tx.currency_original, tx.transaction_date)
            tx.exchange_rate = rate
            tx.amount_base = DomainTransaction.compute_base_amount(
                tx.amount_original, tx.currency_original, rate
            )

        updated = self._tx_repo.update(tx)

        # Keep both legs of a transfer in sync for amount/date/description edits
        if tx.is_transfer and tx.transfer_id:
            for leg in self._tx_repo.find_by_transfer_id(tx.transfer_id, user_id):
                if leg.id == tx.id:
                    continue
                leg.amount_original = updated.amount_original
                leg.currency_original = updated.currency_original
                leg.amount_base = updated.amount_base
                leg.exchange_rate = updated.exchange_rate
                leg.transaction_date = updated.transaction_date
                leg.description = updated.description
                self._tx_repo.update(leg)

        return updated

    def delete(self, tx_id: UUID, user_id: UUID) -> None:
        tx = self.get(tx_id, user_id)
        if tx.is_transfer and tx.transfer_id:
            # Removing one leg of a transfer must remove the other, otherwise
            # money would appear or vanish from one of the wallets.
            for leg in self._tx_repo.find_by_transfer_id(tx.transfer_id, user_id):
                self._tx_repo.soft_delete(leg.id, user_id)
            return
        self._tx_repo.soft_delete(tx_id, user_id)
