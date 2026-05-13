from fastapi import FastAPI

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

app = FastAPI(title="ZeroWhisper", version="0.1.0")

app.add_middleware(SetupGuardMiddleware)

app.include_router(setup_router.router, prefix="/setup", tags=["setup"])
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(tx_router.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(imports_router.router, prefix="/api/imports", tags=["imports"])
app.include_router(rates_router.router, prefix="/api/exchange-rates", tags=["exchange-rates"])
app.include_router(apikeys_router.router, prefix="/api/api-keys", tags=["api-keys"])
app.include_router(mcp_router.router, prefix="/mcp", tags=["mcp"])
app.include_router(whisper_router.router, prefix="/api/whisper", tags=["whisper"])
app.include_router(dashboard_router.router, prefix="/api/dashboard", tags=["dashboard"])


@app.get("/health")
def health():
    return {"status": "ok"}
