"""
Maps domain exceptions to HTTP responses.

Centralized error handling so individual route handlers never need
try/except for domain exceptions.
"""
from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ConflictError,
    DatabaseNotReadyError,
    DomainError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    mapping = {
        NotFoundError: status.HTTP_404_NOT_FOUND,
        UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
        ConflictError: status.HTTP_409_CONFLICT,
        ValidationError: status.HTTP_400_BAD_REQUEST,
        DatabaseNotReadyError: status.HTTP_503_SERVICE_UNAVAILABLE,
    }
    status_code = mapping.get(type(exc), status.HTTP_400_BAD_REQUEST)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.detail, "context": exc.context},
    )
