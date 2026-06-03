"""Auth API routes — register, login, token refresh."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.application.auth_service import AuthService
from app.core.domain.user import User
from app.core.ratelimit import auth_rate_limit
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, RefreshRequest, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_service(request: Request, session: Session = Depends(get_session)) -> AuthService:
    return request.app.state.container.auth_service(session)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    request: Request,
    body: UserRegister,
    session: Session = Depends(get_session),
    _: None = Depends(auth_rate_limit),
):
    service: AuthService = request.app.state.container.auth_service(session)
    user = service.register(body.username, body.email, body.password)

    # Seed default categories for new user
    cat_service = request.app.state.container.category_service(session)
    cat_service.list_or_seed(user.id)

    return UserRead(
        id=str(user.id),
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    body: UserLogin,
    session: Session = Depends(get_session),
    _: None = Depends(auth_rate_limit),
):
    service: AuthService = request.app.state.container.auth_service(session)
    user = service.authenticate(body.username, body.password)
    return TokenResponse(
        access_token=service.create_access_token(user.id),
        refresh_token=service.create_refresh_token(user.id),
    )


@router.post("/refresh")
def refresh(
    body: RefreshRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    service: AuthService = request.app.state.container.auth_service(session)
    user_id = service.decode_token(body.refresh_token, "refresh")
    new_access_token = service.create_access_token(user_id)
    return {"access_token": new_access_token, "token_type": "bearer"}
