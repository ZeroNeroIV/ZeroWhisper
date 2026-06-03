from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class Wallet(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    name: str = Field(max_length=128)
    currency: str = Field(default="JOD", max_length=3)
    balance: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=6)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
