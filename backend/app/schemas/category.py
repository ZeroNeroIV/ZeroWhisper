from uuid import UUID
from typing import Optional, Literal

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    type: Literal["income", "expense", "savings"]
    color: Optional[str] = None
    icon: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    type: Optional[Literal["income", "expense", "savings"]] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class CategoryRead(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    type: str
    color: str | None
    icon: str | None
    is_default: bool
