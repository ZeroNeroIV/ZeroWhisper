"""
ZeroWhisper — application entry point (composition root).

This file is the only place where:
1. The DI Container is created and wired
2. FastAPI is configured with routes and middleware
3. Lifespan hooks for startup/shutdown are defined
4. Error handlers are registered

No business logic lives here. No domain exceptions are raised here.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.container import Container
from app.api.error_handlers import domain_error_handler
from app.core.exceptions import DatabaseNotReadyError, DomainError

logger = logging.getLogger(__name__)

_CONTAINER: Container | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _CONTAINER
    _CONTAINER = Container()
    app.state.container = _CONTAINER

    # Load runtime AI settings
    from app.infrastructure import ai_settings
    ai_settings.load()

    # Auto-unlock any open vaults
    _CONTAINER.vault_manager.auto_unlock_open_vaults()

    # Start background scheduler
    from app.scheduler import start_bank_sync_scheduler
    scheduler_task = start_bank_sync_scheduler(_CONTAINER.db, _CONTAINER)

    logger.info("ZeroWhisper started — vault ready: %s", _CONTAINER.vault_manager.is_db_ready())
    yield

    scheduler_task.cancel()
    _CONTAINER.db.dispose()


app = FastAPI(
    title="ZeroWhisper",
    version="0.2.0",
    lifespan=lifespan,
)

# ── Global error handlers ─────────────────────────────────────────────────────

app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

# Also catch raw pysqlcipher3 DatabaseError for the old code path
@app.exception_handler(Exception)
async def catchall_error_handler(request: Request, exc: Exception) -> JSONResponse:
    try:
        import pysqlcipher3.dbapi2 as _psc
        if isinstance(exc, _psc.DatabaseError):
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Database unavailable. Please unlock the database via /setup/unlock.",
                    "context": {"wrapped": str(exc)},
                },
            )
    except ImportError:
        pass
    raise exc


# ── Middleware ────────────────────────────────────────────────────────────────

@app.middleware("http")
async def setup_guard_middleware(request: Request, call_next):
    """Block requests to protected endpoints when the DB is not ready."""
    path = request.url.path
    always_allowed = {
        "/health", "/setup/status", "/setup/initialize", "/setup/unlock",
        "/setup/recover", "/setup/vaults", "/docs", "/openapi.json", "/redoc",
    }
    if any(path == p or path.startswith(p) for p in always_allowed):
        return await call_next(request)

    if not _CONTAINER or not _CONTAINER.vault_manager.is_db_ready():
        return JSONResponse(
            status_code=503,
            content={"detail": "Database not ready. Complete setup at /setup/initialize"},
        )
    return await call_next(request)


# ── Routes ────────────────────────────────────────────────────────────────────

from app.api.routes.setup import router as setup_router
from app.api.routes.imports import router as imports_router
from app.api.routes.api_keys import router as api_keys_router
from app.api.routes.ai_settings import router as ai_settings_router
from app.api.routes.banks import router as banks_router
from app.api.routes.transactions import router as tx_router
from app.api.routes.whisper import router as whisper_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.categories import router as categories_router
from app.api.routes.exchange_rates import router as exchange_rates_router
from app.api.routes.auth import router as auth_router
from app.api.routes.mcp import router as mcp_router
from app.api.routes.wallets import router as wallets_router

app.include_router(setup_router, prefix="/setup", tags=["setup"])
app.include_router(imports_router)
app.include_router(api_keys_router)
app.include_router(ai_settings_router)
app.include_router(banks_router)
app.include_router(tx_router)
app.include_router(whisper_router)
app.include_router(analytics_router)
app.include_router(dashboard_router)
app.include_router(categories_router)
app.include_router(exchange_rates_router)
app.include_router(auth_router)
app.include_router(mcp_router)
app.include_router(wallets_router)


@app.get("/health")
def health():
    return {"status": "ok"}
