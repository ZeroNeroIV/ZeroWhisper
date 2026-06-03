"""
CategoryRepository port — abstract persistence contract for categories.

Why separate from TransactionRepository?
- Category queries are accessed by analytics, MCP, and transaction services
- The type_map pattern (category name -> type) was duplicated in every analytics function
- Category seeding (defaults) is a domain concept that the repo should support
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.category import Category, CategoryType


class CategoryRepository(ABC):

    @abstractmethod
    def find_by_user(self, user_id: UUID) -> list[Category]:
        ...

    @abstractmethod
    def find_by_id(self, cat_id: UUID, user_id: UUID) -> Category | None:
        ...

    @abstractmethod
    def find_by_name(self, user_id: UUID, name: str) -> Category | None:
        ...

    @abstractmethod
    def save(self, category: Category) -> Category:
        ...

    @abstractmethod
    def update(self, category: Category) -> Category:
        ...

    @abstractmethod
    def delete(self, cat_id: UUID, user_id: UUID) -> None:
        """Delete category. Raises ConflictError if transactions reference it."""
        ...

    @abstractmethod
    def get_type_map(self, user_id: UUID) -> dict[str, str]:
        """Return {category_name -> type_string} for all user categories."""
        ...

    @abstractmethod
    def find_by_type(self, user_id: UUID, type: CategoryType) -> list[Category]:
        ...

    @abstractmethod
    def seed_defaults(self, user_id: UUID) -> list[Category]:
        """Create default categories if none exist. Returns created categories."""
        ...
