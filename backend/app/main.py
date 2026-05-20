from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings  # noqa: F401 — triggers env loading
from app.middleware.setup_guard import SetupGuardMiddleware
from app.routers import setup as setup_router
from app.routers import auth as auth_router
from app.routers import transactions as tx_router
from app.routers import imports as imports_router
from app.routers import exchange_rates as rates_router
from app.routers import api_keys as apikeys_router
from app.routers import mcp as mcp_router
from app.routers import whisper as whisper_router
from app.routers import dashboard as dashboard_router
from app.routers import analytics as analytics_router
from app.routers import ai_settings as ai_settings_router

@asynccontextmanager
async def lifespan(_: FastAPI):
    from app.services import setup as setup_service, ai_settings_service
    ai_settings_service.load()
    setup_service.auto_unlock_open_vaults()
    yield


app = FastAPI(title="ZeroWhisper", version="0.1.0", lifespan=lifespan)

app.add_middleware(SetupGuardMiddleware)


@app.exception_handler(Exception)
async def database_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Catch pysqlcipher3 DatabaseError (and any other unexpected DB error) so
    # the client gets a structured JSON response instead of FastAPI's bare 500.
    try:
        import pysqlcipher3.dbapi2 as _psc  # type: ignore[import-untyped]
        if isinstance(exc, _psc.DatabaseError):
            return JSONResponse(
                status_code=503,
                content={"detail": "Database unavailable. Please unlock the database via /setup/unlock."},
            )
    except ImportError:
        pass
    raise exc

app.include_router(setup_router.router, prefix="/setup", tags=["setup"])
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(tx_router.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(imports_router.router, prefix="/api/imports", tags=["imports"])
app.include_router(rates_router.router, prefix="/api/exchange-rates", tags=["exchange-rates"])
app.include_router(apikeys_router.router, prefix="/api/api-keys", tags=["api-keys"])
app.include_router(mcp_router.router, prefix="/mcp", tags=["mcp"])
app.include_router(whisper_router.router, prefix="/api/whisper", tags=["whisper"])
app.include_router(dashboard_router.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(analytics_router.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(ai_settings_router.router, prefix="/api/ai-settings", tags=["ai-settings"])


@app.get("/health")
def health():
    return {"status": "ok"}
