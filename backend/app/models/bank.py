from datetime import datetime
from app.core.time import utc_now
from uuid import UUID

from sqlmodel import SQLModel, Field


class BankConnection(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    bank_name: str = Field(max_length=128)
    auth_type: str = Field(default="api_key")
    credentials: str = Field(default="{}")
    account_number: str = Field(default="")
    is_active: bool = Field(default=True)
    last_sync_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
