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

    # Top-level defaults plus a starter set of sub-categories ("parent" refers
    # to a top-level name). Users can add their own at either level.
    DEFAULT_CATEGORIES = [
        {"name": "Food & Drinks", "type": "expense", "color": "#ef4444", "icon": "🍕"},
        {"name": "Transportation", "type": "expense", "color": "#3b82f6", "icon": "🚗"},
        {"name": "Housing", "type": "expense", "color": "#f59e0b", "icon": "🏠"},
        {"name": "Utilities", "type": "expense", "color": "#8b5cf6", "icon": "💡"},
        {"name": "Entertainment", "type": "expense", "color": "#ec4899", "icon": "🎬"},
        {"name": "Shopping", "type": "expense", "color": "#14b8a6", "icon": "🛍️"},
        {"name": "Health", "type": "expense", "color": "#06b6d4", "icon": "🏥"},
        {"name": "Education", "type": "expense", "color": "#a855f7", "icon": "📚"},
        {"name": "Income", "type": "income", "color": "#22c55e", "icon": "💰"},
        {"name": "Salary", "type": "income", "color": "#16a34a", "icon": "💼", "parent": "Income"},
        {"name": "Freelance", "type": "income", "color": "#4ade80", "icon": "🧑‍💻", "parent": "Income"},
        {"name": "Savings", "type": "savings", "color": "#6366f1", "icon": "🏦"},
        {"name": "Family Savings", "type": "savings", "color": "#818cf8", "icon": "👨‍👩‍👧", "parent": "Savings"},
        {"name": "Transfer", "type": "transfer", "color": "#94a3b8", "icon": "🔁"},
        {"name": "Other", "type": "expense", "color": "#6b7280", "icon": "📦"},
    ]

    TRANSFER_CATEGORY_NAME = "Transfer"

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
            parent_id=orm.parent_id,
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
            parent_id=domain.parent_id,
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
        orm.parent_id = category.parent_id
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
        if self.has_children(cat_id, user_id):
            raise ConflictError(f"Category '{orm.name}' has sub-categories; delete or move them first")
        self._session.delete(orm)
        self._session.commit()

    def has_children(self, cat_id: UUID, user_id: UUID) -> bool:
        child = self._session.exec(
            select(ORMCategory).where(
                ORMCategory.user_id == user_id,
                ORMCategory.parent_id == cat_id,
            ).limit(1)
        ).first()
        return child is not None

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
        created: list[DomainCategory] = []
        by_name: dict[str, DomainCategory] = {}
        for data in self.DEFAULT_CATEGORIES:
            parent = by_name.get(data.get("parent", ""))
            cat = DomainCategory(
                user_id=user_id,
                name=data["name"],
                type=CategoryType(data["type"]),
                color=data["color"],
                icon=data["icon"],
                is_default=True,
                parent_id=parent.id if parent else None,
            )
            saved = self.save(cat)
            by_name[saved.name] = saved
            created.append(saved)
        return created

    def get_or_create_transfer_category(self, user_id: UUID) -> DomainCategory:
        """The reserved category used by inter-wallet transfer legs."""
        cat = self.find_by_name(user_id, self.TRANSFER_CATEGORY_NAME)
        if cat:
            return cat
        return self.save(DomainCategory(
            user_id=user_id,
            name=self.TRANSFER_CATEGORY_NAME,
            type=CategoryType.TRANSFER,
            color="#94a3b8",
            icon="🔁",
            is_default=True,
        ))
