import datetime as dt
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Numeric
from sqlmodel import SQLModel, Field


class ExchangeRate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: dt.date = Field(index=True)
    jod_per_usd: Decimal = Field(sa_column=Column(Numeric(precision=18, scale=6)))
    source: str = Field(default="manual")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Transaction(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    amount_original: Decimal = Field(sa_column=Column(Numeric(precision=18, scale=6)))
    currency_original: str = Field(default="JOD")
    amount_base: Decimal = Field(sa_column=Column(Numeric(precision=18, scale=6)))
    exchange_rate: Decimal = Field(
        default=Decimal("1.0"),
        sa_column=Column(Numeric(precision=18, scale=6)),
    )
    category: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    transaction_date: dt.date = Field(index=True)
    source: str = Field(default="manual")
    type: str = Field(default="expense", index=True)
    is_deleted: bool = Field(default=False)
    wallet_id: Optional[UUID] = Field(default=None, foreign_key="wallet.id", index=True)
    transfer_id: Optional[UUID] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
