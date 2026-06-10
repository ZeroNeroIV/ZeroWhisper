from uuid import uuid4, UUID

from sqlmodel import SQLModel, Field, Column, String
from sqlalchemy import UniqueConstraint


class Category(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "name"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    name: str
    type: str = Field(sa_column=Column(String, nullable=False))
    color: str | None = Field(default=None)
    icon: str | None = Field(default=None)
    is_default: bool = Field(default=False)
    parent_id: UUID | None = Field(default=None, foreign_key="category.id")
