"""
Category use cases — CRUD with default seeding.

Owns the business rules around category management:
- Default categories are seeded on first access if empty
- Categories in use by transactions cannot be deleted
- Category type must be one of income/expense/savings
"""
from __future__ import annotations

from uuid import UUID

from app.core.domain.category import Category, CategoryType
from app.core.exceptions import NotFoundError, ConflictError
from app.core.ports.category_repo import CategoryRepository


class CategoryService:

    def __init__(self, cat_repo: CategoryRepository) -> None:
        self._cat_repo = cat_repo

    def list_or_seed(self, user_id: UUID) -> list[Category]:
        """Get categories for a user, seeding defaults if none exist."""
        return self._cat_repo.seed_defaults(user_id)

    def get(self, cat_id: UUID, user_id: UUID) -> Category:
        cat = self._cat_repo.find_by_id(cat_id, user_id)
        if not cat:
            raise NotFoundError("Category", str(cat_id))
        return cat

    def create(
        self,
        user_id: UUID,
        name: str,
        type: CategoryType,
        color: str | None = None,
        icon: str | None = None,
    ) -> Category:
        cat = Category(
            user_id=user_id,
            name=name,
            type=type,
            color=color,
            icon=icon,
        )
        return self._cat_repo.save(cat)

    def update(
        self,
        cat_id: UUID,
        user_id: UUID,
        *,
        name: str | None = None,
        type: CategoryType | None = None,
        color: str | None = None,
        icon: str | None = None,
    ) -> Category:
        existing = self.get(cat_id, user_id)
        if name is not None:
            existing.name = name
        if type is not None:
            existing.type = type
        if color is not None:
            existing.color = color
        if icon is not None:
            existing.icon = icon
        return self._cat_repo.update(existing)

    def delete(self, cat_id: UUID, user_id: UUID) -> None:
        self._cat_repo.delete(cat_id, user_id)
