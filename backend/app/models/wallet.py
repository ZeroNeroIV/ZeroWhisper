from datetime import datetime
from app.core.time import utc_now
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Numeric
from sqlmodel import SQLModel, Field


class Wallet(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    name: str = Field(max_length=128)
    type: str = Field(default="cash", index=True)
    currency: str = Field(default="JOD", max_length=3)
    balance: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=18, scale=6)),
    )
    initial_balance: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=18, scale=6)),
    )
    icon: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
