from datetime import datetime
from pydantic import BaseModel


class BankConnectionCreate(BaseModel):
    bank_name: str
    auth_type: str = "api_key"
    credentials: dict = {}
    account_number: str = ""


class BankConnectionUpdate(BaseModel):
    is_active: bool | None = None
    credentials: dict | None = None
    account_number: str | None = None


class BankConnectionRead(BaseModel):
    id: int
    bank_name: str
    auth_type: str
    account_number: str
    is_active: bool
    last_sync_at: datetime | None
    created_at: datetime
