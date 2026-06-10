"""
FastAPI dependencies — wires the container to request handlers.

Every dependency here is a factory that pulls services from the container
and provides them to route handlers. No business logic — pure plumbing.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.api.container import Container
from app.core.domain.user import User
from app.core.exceptions import DomainError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_container(request: Request) -> Container:
    return request.app.state.container  # type: ignore[no-any-return]


ContainerDep = Annotated[Container, Depends(get_container)]


def get_session(container: ContainerDep) -> Session:
    for session in container.db.get_session():
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


# ── Current user (JWT) ──────────────────────────────────────────────────────────


def get_current_user(
    container: ContainerDep,
    session: SessionDep,
    token: str = Depends(oauth2_scheme),
) -> User:
    service = container.auth_service(session)
    try:
        return service.verify_token(token)
    except DomainError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Current user (API key) ──────────────────────────────────────────────────────


def get_current_user_by_api_key(
    container: ContainerDep,
    session: SessionDep,
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> User:
    service = container.api_key_service(session)
    user = service.verify(x_api_key)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )
    return user


UserDep = Annotated[User, Depends(get_current_user)]
ApiKeyUserDep = Annotated[User, Depends(get_current_user_by_api_key)]
