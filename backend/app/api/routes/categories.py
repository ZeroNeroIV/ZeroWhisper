from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import ContainerDep, SessionDep, UserDep
from app.application.category_service import CategoryService
from app.core.domain.category import CategoryType
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryRead

router = APIRouter(prefix="/api/categories", tags=["categories"])


def _to_read(cat) -> CategoryRead:
    return CategoryRead(
        id=cat.id,
        user_id=cat.user_id,
        name=cat.name,
        type=cat.type.value,
        color=cat.color,
        icon=cat.icon,
        is_default=cat.is_default,
        parent_id=cat.parent_id,
    )


@router.get("", response_model=list[CategoryRead])
def list_categories(
    container: ContainerDep,
    session: SessionDep,
    user: UserDep,
):
    service: CategoryService = container.category_service(session)
    return service.list_or_seed(user.id)


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    container: ContainerDep,
    session: SessionDep,
    body: CategoryCreate,
    user: UserDep,
):
    service: CategoryService = container.category_service(session)
    cat = service.create(
        user_id=user.id,
        name=body.name,
        type=CategoryType(body.type),
        color=body.color,
        icon=body.icon,
        parent_id=body.parent_id,
    )
    return _to_read(cat)


@router.put("/{cat_id}", response_model=CategoryRead)
def update_category(
    container: ContainerDep,
    session: SessionDep,
    cat_id: UUID,
    body: CategoryUpdate,
    user: UserDep,
):
    service: CategoryService = container.category_service(session)
    cat = service.update(
        cat_id=cat_id,
        user_id=user.id,
        name=body.name,
        type=CategoryType(body.type) if body.type else None,
        color=body.color,
        icon=body.icon,
        parent_id=body.parent_id,
        clear_parent=body.clear_parent,
    )
    return _to_read(cat)


@router.delete("/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    container: ContainerDep,
    session: SessionDep,
    cat_id: UUID,
    user: UserDep,
):
    service: CategoryService = container.category_service(session)
    service.delete(cat_id, user.id)
