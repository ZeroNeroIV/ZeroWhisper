"""
FastAPI dependencies — wires the container to request handlers.

Every dependency here is a factory that pulls services from the container
and provides them to route handlers. No business logic — pure plumbing.
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.api.container import Container
from app.application.auth_service import AuthService
from app.application.transaction_service import TransactionService
from app.application.whisper_service import WhisperService
from app.application.analytics_service import AnalyticsService
from app.application.mcp_service import MCPService
from app.application.category_service import CategoryService
from app.application.exchange_rate_service import ExchangeRateService
from app.application.csv_import_service import CsvImportService
from app.application.bank_sync_service import BankSyncService
from app.core.domain.user import User
from app.core.exceptions import DomainError
from app.infrastructure.database import DatabaseManager

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _get_container(request: Request) -> Container:
    return request.app.state.container  # type: ignore[no-any-return]


def _get_db(request: Request) -> DatabaseManager:
    return request.app.state.container.db


def get_session(db: Annotated[DatabaseManager, Depends(_get_db)]) -> Session:
    """FastAPI-compatible session generator."""
    for session in db.get_session():
        yield session


# ── Current user (JWT) ──────────────────────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    request: Request = Depends(_get_container),
    session: Session = Depends(get_session),
) -> User:
    container: Container = request
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
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key"),
    session: Session = Depends(get_session),
) -> User:
    from app.application.api_key_service import ApiKeyService
    from app.infrastructure.repositories.api_key_repo import SQLModelApiKeyRepository

    svc = ApiKeyService(SQLModelApiKeyRepository(session))
    user = svc.verify(x_api_key)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )
    return user


# ── Service factories (per request, with session) ──────────────────────────────

def _get_tx_service(
    request: Request,
    session: Session = Depends(get_session),
) -> TransactionService:
    return request.app.state.container.transaction_service(session)


def _get_whisper_service(
    request: Request,
    session: Session = Depends(get_session),
) -> WhisperService:
    return request.app.state.container.whisper_service(session)


def _get_analytics_service(
    request: Request,
    session: Session = Depends(get_session),
) -> AnalyticsService:
    return request.app.state.container.analytics_service(session)


def _get_mcp_service(
    request: Request,
    session: Session = Depends(get_session),
) -> MCPService:
    return request.app.state.container.mcp_service(session)


def _get_category_service(
    request: Request,
    session: Session = Depends(get_session),
) -> CategoryService:
    return request.app.state.container.category_service(session)


def _get_exchange_rate_service(
    request: Request,
    session: Session = Depends(get_session),
) -> ExchangeRateService:
    return request.app.state.container.exchange_rate_service(session)


def _get_csv_import_service(
    request: Request,
    session: Session = Depends(get_session),
) -> CsvImportService:
    return request.app.state.container.csv_import_service(session)


def _get_bank_sync_service(
    request: Request,
    session: Session = Depends(get_session),
) -> BankSyncService:
    return request.app.state.container.bank_sync_service(session)
