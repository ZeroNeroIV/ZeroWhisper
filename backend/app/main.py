from fastapi import FastAPI

from app.config import settings  # noqa: F401 — imported for side-effects (env loading)
from app.middleware.setup_guard import SetupGuardMiddleware
from app.routers import setup as setup_router

app = FastAPI(title="ZeroWhisper", version="0.1.0")

app.add_middleware(SetupGuardMiddleware)
app.include_router(setup_router.router, prefix="/setup", tags=["setup"])


@app.get("/health")
def health():
    return {"status": "ok"}
