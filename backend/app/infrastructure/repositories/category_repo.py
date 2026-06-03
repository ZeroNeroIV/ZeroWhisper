"""SQLModel-backed CategoryRepository implementation."""
from __future__ import annotations

from uuid import UUID
from sqlmodel import Session, select
from app.core.domain.category import Category as DomainCategory, CategoryType
from app.core.exceptions import ConflictError, NotFoundError
from app.core.ports.category_repo import CategoryRepository
from app.models.category import Category as ORMCategory
from app.models.transaction import Transaction


class SQLModelCategoryRepository(CategoryRepository):

    DEFAULT_CATEGORIES = [
        {"name": "Food", "type": "expense", "color": "#ef4444", "icon": "🍕"},
        {"name": "Transport", "type": "expense", "color": "#3b82f6", "icon": "🚗"},
        {"name": "Housing", "type": "expense", "color": "#f59e0b", "icon": "🏠"},
        {"name": "Utilities", "type": "expense", "color": "#8b5cf6", "icon": "💡"},
        {"name": "Entertainment", "type": "expense", "color": "#ec4899", "icon": "🎬"},
        {"name": "Shopping", "type": "expense", "color": "#14b8a6", "icon": "🛍️"},
        {"name": "Health", "type": "expense", "color": "#06b6d4", "icon": "🏥"},
        {"name": "Education", "type": "expense", "color": "#a855f7", "icon": "📚"},
        {"name": "Income", "type": "income", "color": "#22c55e", "icon": "💰"},
        {"name": "Savings", "type": "savings", "color": "#6366f1", "icon": "🏦"},
        {"name": "Other", "type": "expense", "color": "#6b7280", "icon": "📦"},
    ]

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: ORMCategory) -> DomainCategory:
        return DomainCategory(
            id=orm.id,
            user_id=orm.user_id,
            name=orm.name,
            type=CategoryType(orm.type),
            color=orm.color,
            icon=orm.icon,
            is_default=orm.is_default,
        )

    @staticmethod
    def _to_orm(domain: DomainCategory) -> ORMCategory:
        return ORMCategory(
            id=domain.id,
            user_id=domain.user_id,
            name=domain.name,
            type=domain.type.value,
            color=domain.color,
            icon=domain.icon,
            is_default=domain.is_default,
        )

    def find_by_user(self, user_id: UUID) -> list[DomainCategory]:
        items = self._session.exec(
            select(ORMCategory).where(ORMCategory.user_id == user_id)
        ).all()
        return [self._to_domain(c) for c in items]

    def find_by_id(self, cat_id: UUID, user_id: UUID) -> DomainCategory | None:
        result = self._session.exec(
            select(ORMCategory).where(
                ORMCategory.id == cat_id,
                ORMCategory.user_id == user_id,
            )
        ).first()
        return self._to_domain(result) if result else None

    def find_by_name(self, user_id: UUID, name: str) -> DomainCategory | None:
        result = self._session.exec(
            select(ORMCategory).where(
                ORMCategory.user_id == user_id,
                ORMCategory.name == name,
            )
        ).first()
        return self._to_domain(result) if result else None

    def save(self, category: DomainCategory) -> DomainCategory:
        orm = self._to_orm(category)
        self._session.add(orm)
        self._session.commit()
        self._session.refresh(orm)
        return self._to_domain(orm)

    def update(self, category: DomainCategory) -> DomainCategory:
        orm = self._session.exec(
            select(ORMCategory).where(
                ORMCategory.id == category.id,
                ORMCategory.user_id == category.user_id,
            )
        ).first()
        if not orm:
            raise NotFoundError("Category", str(category.id))
        orm.name = category.name
        orm.type = category.type.value
        orm.color = category.color
        orm.icon = category.icon
        self._session.add(orm)
        self._session.commit()
        self._session.refresh(orm)
        return self._to_domain(orm)

    def delete(self, cat_id: UUID, user_id: UUID) -> None:
        orm = self._session.exec(
            select(ORMCategory).where(
                ORMCategory.id == cat_id,
                ORMCategory.user_id == user_id,
            )
        ).first()
        if not orm:
            raise NotFoundError("Category", str(cat_id))
        # Check for transactions referencing this category
        tx = self._session.exec(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.category == orm.name,
                Transaction.is_deleted == False,
            ).limit(1)
        ).first()
        if tx:
            raise ConflictError(f"Category '{orm.name}' is in use by transactions")
        self._session.delete(orm)
        self._session.commit()

    def get_type_map(self, user_id: UUID) -> dict[str, str]:
        items = self.find_by_user(user_id)
        return {c.name: c.type.value for c in items}

    def find_by_type(self, user_id: UUID, type: CategoryType) -> list[DomainCategory]:
        items = self._session.exec(
            select(ORMCategory).where(
                ORMCategory.user_id == user_id,
                ORMCategory.type == type.value,
            )
        ).all()
        return [self._to_domain(c) for c in items]

    def seed_defaults(self, user_id: UUID) -> list[DomainCategory]:
        existing = self.find_by_user(user_id)
        if existing:
            return existing
        created = []
        for data in self.DEFAULT_CATEGORIES:
            cat = DomainCategory(
                user_id=user_id,
                name=data["name"],
                type=CategoryType(data["type"]),
                color=data["color"],
                icon=data["icon"],
                is_default=True,
            )
            created.append(self.save(cat))
        return created
