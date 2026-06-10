from decimal import Decimal
from datetime import date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

VALID_CURRENCIES = ["JOD", "USD"]


class TransactionCreate(BaseModel):
    amount_original: Decimal = Field(..., gt=0)
    currency_original: str = Field(..., description="JOD or USD")
    category: str
    description: Optional[str] = None
    transaction_date: date
    wallet_id: Optional[UUID] = None

    @field_validator("currency_original")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v not in VALID_CURRENCIES:
            raise ValueError(f"currency_original must be one of {VALID_CURRENCIES}")
        return v


class TransactionUpdate(BaseModel):
    amount_original: Optional[Decimal] = Field(None, gt=0)
    currency_original: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    transaction_date: Optional[date] = None
    wallet_id: Optional[UUID] = None

    @field_validator("currency_original")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_CURRENCIES:
            raise ValueError(f"currency_original must be one of {VALID_CURRENCIES}")
        return v


class TransactionRead(BaseModel):
    id: UUID
    user_id: UUID
    amount_original: Decimal
    currency_original: str
    amount_base: Decimal
    exchange_rate: Decimal
    category: str
    description: Optional[str]
    transaction_date: date
    source: str
    type: str
    wallet_id: Optional[UUID] = None
    transfer_id: Optional[UUID] = None
    created_at: str  # ISO format


def tx_to_read(tx) -> TransactionRead:
    """Map a domain Transaction to its API representation."""
    return TransactionRead(
        id=tx.id, user_id=tx.user_id, amount_original=tx.amount_original,
        currency_original=tx.currency_original, amount_base=tx.amount_base,
        exchange_rate=tx.exchange_rate, category=tx.category,
        description=tx.description, transaction_date=tx.transaction_date,
        source=tx.source, type=tx.type.value, wallet_id=tx.wallet_id,
        transfer_id=tx.transfer_id, created_at=tx.created_at.isoformat(),
    )


class PaginatedTransactions(BaseModel):
    items: list[TransactionRead]
    total: int
    page: int
    page_size: int
    pages: int
