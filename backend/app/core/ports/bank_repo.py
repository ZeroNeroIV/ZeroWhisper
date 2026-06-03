"""
BankConnectionRepository port — abstract persistence contract for bank connections.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class BankConnectionData:
    def __init__(self, id: int, bank_name: str, auth_type: str, account_number: str,
                 is_active: bool, last_sync_at: datetime | None, created_at: datetime,
                 credentials: dict, user_id: UUID) -> None:
        self.id = id
        self.bank_name = bank_name
        self.auth_type = auth_type
        self.account_number = account_number
        self.is_active = is_active
        self.last_sync_at = last_sync_at
        self.created_at = created_at
        self.credentials = credentials
        self.user_id = user_id


class BankConnectionRepository(ABC):

    @abstractmethod
    def list_by_user(self, user_id: UUID) -> list[BankConnectionData]:
        ...

    @abstractmethod
    def get(self, conn_id: int, user_id: UUID) -> BankConnectionData | None:
        ...

    @abstractmethod
    def create(self, user_id: UUID, bank_name: str, auth_type: str,
               account_number: str, credentials: dict) -> BankConnectionData:
        ...

    @abstractmethod
    def update(self, conn_id: int, user_id: UUID, **kwargs) -> BankConnectionData | None:
        ...

    @abstractmethod
    def delete(self, conn_id: int, user_id: UUID) -> bool:
        ...
