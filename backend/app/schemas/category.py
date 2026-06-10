from uuid import UUID
from typing import Optional, Literal

from pydantic import BaseModel, Field

CategoryTypeLiteral = Literal["income", "expense", "savings", "transfer"]


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    type: CategoryTypeLiteral
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[UUID] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    type: Optional[CategoryTypeLiteral] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[UUID] = None
    clear_parent: bool = False


class CategoryRead(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    type: str
    color: str | None
    icon: str | None
    is_default: bool
    parent_id: UUID | None = None
