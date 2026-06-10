from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import ContainerDep, SessionDep
from app.application.auth_service import AuthService
from app.core.ratelimit import auth_rate_limit
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, RefreshRequest, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    container: ContainerDep,
    session: SessionDep,
    body: UserRegister,
    _: None = Depends(auth_rate_limit),
):
    service: AuthService = container.auth_service(session)
    user = service.register(body.username, body.email, body.password)
    # Seed default categories at account creation so Whisper, bank sync and
    # the UI never have to write during a read path.
    container.category_repo(session).seed_defaults(user.id)
    return UserRead(
        id=str(user.id),
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    container: ContainerDep,
    session: SessionDep,
    body: UserLogin,
    _: None = Depends(auth_rate_limit),
):
    service: AuthService = container.auth_service(session)
    user = service.authenticate(body.username, body.password)
    return TokenResponse(
        access_token=service.create_access_token(user.id),
        refresh_token=service.create_refresh_token(user.id),
    )


@router.post("/refresh")
def refresh(
    container: ContainerDep,
    session: SessionDep,
    body: RefreshRequest,
):
    service: AuthService = container.auth_service(session)
    user_id = service.decode_token(body.refresh_token, "refresh")
    new_access_token = service.create_access_token(user_id)
    return {"access_token": new_access_token, "token_type": "bearer"}
