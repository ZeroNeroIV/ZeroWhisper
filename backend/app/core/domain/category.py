from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class CategoryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    SAVINGS = "savings"
    TRANSFER = "transfer"


@dataclass
class Category:
    user_id: UUID
    name: str
    type: CategoryType
    color: str | None = None
    icon: str | None = None
    is_default: bool = False
    parent_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
