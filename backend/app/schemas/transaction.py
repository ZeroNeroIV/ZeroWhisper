from decimal import Decimal
from datetime import date
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES = ["Food", "Transport", "Housing", "Utilities", "Entertainment",
                    "Shopping", "Health", "Education", "Income", "Other"]

VALID_CURRENCIES = ["JOD", "USD"]


class TransactionCreate(BaseModel):
    amount_original: Decimal = Field(..., gt=0)
    currency_original: str = Field(..., description="JOD or USD")
    category: str
    description: Optional[str] = None
    transaction_date: date

    @field_validator("currency_original")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v not in VALID_CURRENCIES:
            raise ValueError(f"currency_original must be one of {VALID_CURRENCIES}")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {VALID_CATEGORIES}")
        return v


class TransactionUpdate(BaseModel):
    amount_original: Optional[Decimal] = Field(None, gt=0)
    currency_original: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    transaction_date: Optional[date] = None

    @field_validator("currency_original")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_CURRENCIES:
            raise ValueError(f"currency_original must be one of {VALID_CURRENCIES}")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {VALID_CATEGORIES}")
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
    created_at: str  # ISO format


class PaginatedTransactions(BaseModel):
    items: list[TransactionRead]
    total: int
    page: int
    page_size: int
    pages: int
