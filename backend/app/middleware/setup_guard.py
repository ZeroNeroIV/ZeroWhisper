"""
SetupGuardMiddleware — blocks requests to protected endpoints when the DB is
not ready (key not loaded in memory).

Setup endpoints, health, and API docs are always allowed through.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.services import setup as setup_service

ALWAYS_ALLOWED = {
    "/health",
    "/setup/status",
    "/setup/initialize",
    "/setup/unlock",
    "/setup/recover",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class SetupGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path == p or path.startswith(p) for p in ALWAYS_ALLOWED):
            return await call_next(request)

        if not setup_service.is_db_ready():
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Database not ready. Complete setup at /setup/initialize"
                },
            )

        return await call_next(request)
