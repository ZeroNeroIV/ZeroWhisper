"""
Domain exceptions — NOT tied to HTTP.

Every exception here represents a business-domain failure that the API layer
maps to an appropriate HTTP status code. Service code must NEVER raise
HTTPException directly.

Why not HTTPException factories (like the old exceptions.py)?
- Domain logic should not import FastAPI
- HTTP status codes are a presentation concern, not a domain concern
- Services may be called from non-HTTP entrypoints (MCP, CLI, tests)
"""
from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """Base for all domain exceptions."""

    detail: str
    context: dict[str, Any] | None

    def __init__(self, detail: str, context: dict[str, Any] | None = None) -> None:
        self.detail = detail
        self.context = context
        super().__init__(detail)


class NotFoundError(DomainError):
    """Entity not found by the given identifier."""

    def __init__(
        self,
        entity: str,
        identifier: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        detail = f"{entity} not found"
        if identifier:
            detail += f": {identifier}"
        super().__init__(detail=detail, context=context)


class UnauthorizedError(DomainError):
    """Authentication required or credentials invalid."""

    def __init__(
        self,
        detail: str = "Not authenticated",
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail=detail, context=context)


class ForbiddenError(DomainError):
    """Authenticated but not authorized for this action."""

    def __init__(
        self,
        detail: str = "Forbidden",
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail=detail, context=context)


class ConflictError(DomainError):
    """Request conflicts with current state (e.g. duplicate)."""

    def __init__(
        self,
        detail: str = "Conflict",
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail=detail, context=context)


class ValidationError(DomainError):
    """Input validation failure."""

    def __init__(
        self,
        detail: str = "Validation failed",
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail=detail, context=context)


class DatabaseNotReadyError(DomainError):
    """Database engine not initialized yet (setup not complete)."""

    def __init__(self, detail: str = "Database not ready") -> None:
        super().__init__(detail=detail)


class AIServiceError(DomainError):
    """AI provider call failed (network, auth, rate limit, etc.)."""

    def __init__(
        self,
        detail: str = "AI service call failed",
        wrapped: Exception | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = dict(context or {})
        if wrapped:
            ctx["wrapped"] = str(wrapped)
        super().__init__(detail=detail, context=ctx)
