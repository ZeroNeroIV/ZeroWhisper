from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.user import User


class UserRepository(ABC):

    @abstractmethod
    def find_by_id(self, user_id: UUID) -> User | None:
        ...

    @abstractmethod
    def find_by_username(self, username: str) -> User | None:
        ...

    @abstractmethod
    def find_by_username_or_email(self, username: str, email: str) -> User | None:
        ...

    @abstractmethod
    def save(self, user: User) -> User:
        ...
