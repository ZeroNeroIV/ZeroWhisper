"""Category API routes — thin HTTP glue for category CRUD."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.application.category_service import CategoryService
from app.core.domain.user import User
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


def _get_service(request: Request, session: Session = Depends(get_session)) -> CategoryService:
    return request.app.state.container.category_service(session)


@router.get("", response_model=list[CategoryRead])
def list_categories(
    request: Request,
    user: User = Depends(get_current_user),
    service: CategoryService = Depends(_get_service),
):
    return service.list_or_seed(user.id)


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    request: Request,
    body: CategoryCreate,
    user: User = Depends(get_current_user),
    service: CategoryService = Depends(_get_service),
):
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
    request: Request,
    cat_id: UUID,
    body: CategoryUpdate,
    user: User = Depends(get_current_user),
    service: CategoryService = Depends(_get_service),
):
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
    request: Request,
    cat_id: UUID,
    user: User = Depends(get_current_user),
    service: CategoryService = Depends(_get_service),
):
    service.delete(cat_id, user.id)
