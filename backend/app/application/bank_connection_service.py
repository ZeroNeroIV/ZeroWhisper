"""
Bank connection management use case — CRUD for bank connections.
"""
from __future__ import annotations

from uuid import UUID

from app.core.ports.bank_repo import BankConnectionData, BankConnectionRepository


class BankService:

    def __init__(self, repo: BankConnectionRepository) -> None:
        self._repo = repo

    def list_connections(self, user_id: UUID) -> list[BankConnectionData]:
        return self._repo.list_by_user(user_id)

    def get_connection(self, conn_id: int, user_id: UUID) -> BankConnectionData | None:
        return self._repo.get(conn_id, user_id)

    def create_connection(self, user_id: UUID, bank_name: str, auth_type: str,
                          account_number: str, credentials: dict) -> BankConnectionData:
        return self._repo.create(user_id, bank_name, auth_type, account_number, credentials)

    def update_connection(self, conn_id: int, user_id: UUID,
                          **kwargs) -> BankConnectionData | None:
        return self._repo.update(conn_id, user_id, **kwargs)

    def delete_connection(self, conn_id: int, user_id: UUID) -> bool:
        return self._repo.delete(conn_id, user_id)
