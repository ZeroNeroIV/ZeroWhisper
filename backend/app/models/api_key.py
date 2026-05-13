from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlmodel import SQLModel, Field


class ApiKey(SQLModel, table=True):
    __tablename__ = "apikey"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    key_hash: str = Field(index=True)          # SHA-256 hex digest of the raw key
    prefix: str                                  # first 12 chars of raw key (e.g. "zwp_abc12345")
    name: str                                    # human label
    is_active: bool = Field(default=True)
    last_used_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
