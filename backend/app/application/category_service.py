"""
Category use cases — CRUD with default seeding and a two-level hierarchy.

Owns the business rules around category management:
- Default categories (including starter sub-categories) are seeded on first access
- Categories in use by transactions or with sub-categories cannot be deleted
- Category type must be one of income/expense/savings/transfer
- Sub-categories nest exactly one level deep and inherit sanity from their parent
"""
from __future__ import annotations

from uuid import UUID

from app.core.domain.category import Category, CategoryType
from app.core.exceptions import NotFoundError, ValidationError
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

    def _validate_parent(self, user_id: UUID, parent_id: UUID, child_id: UUID | None = None) -> Category:
        parent = self._cat_repo.find_by_id(parent_id, user_id)
        if not parent:
            raise ValidationError("Parent category not found")
        if child_id is not None and parent.id == child_id:
            raise ValidationError("A category cannot be its own parent")
        if parent.parent_id is not None:
            raise ValidationError("Categories can only nest one level deep")
        return parent

    def create(
        self,
        user_id: UUID,
        name: str,
        type: CategoryType,
        color: str | None = None,
        icon: str | None = None,
        parent_id: UUID | None = None,
    ) -> Category:
        if parent_id is not None:
            self._validate_parent(user_id, parent_id)
        cat = Category(
            user_id=user_id,
            name=name,
            type=type,
            color=color,
            icon=icon,
            parent_id=parent_id,
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
        parent_id: UUID | None = None,
        clear_parent: bool = False,
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
        if clear_parent:
            existing.parent_id = None
        elif parent_id is not None:
            if self._cat_repo.has_children(cat_id, user_id):
                raise ValidationError("A category with sub-categories cannot become a sub-category")
            self._validate_parent(user_id, parent_id, child_id=cat_id)
            existing.parent_id = parent_id
        return self._cat_repo.update(existing)

    def delete(self, cat_id: UUID, user_id: UUID) -> None:
        self._cat_repo.delete(cat_id, user_id)
