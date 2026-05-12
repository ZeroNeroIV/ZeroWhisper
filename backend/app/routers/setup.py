"""
Setup router — handles first-run initialization, restart unlock, and recovery.

All endpoints here are exempt from SetupGuardMiddleware so they are reachable
before (and during) the setup flow.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.exceptions import bad_request, conflict
from app.services import setup as setup_service
from app.services.setup import SetupState

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class InitializeRequest(BaseModel):
    passphrase: str = Field(..., min_length=8, description="Master passphrase (min 8 characters)")


class UnlockRequest(BaseModel):
    passphrase: str = Field(..., description="Master passphrase")


class RecoverRequest(BaseModel):
    recovery_phrase: str = Field(..., description="BIP39 recovery phrase (24 words)")
    new_passphrase: str = Field(..., min_length=8, description="New master passphrase (min 8 characters)")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
def get_status():
    """Return the current setup state. Always accessible, no auth required."""
    state = setup_service.get_state()
    if state == SetupState.INITIALIZED:
        return {"state": state.value, "db_ready": setup_service.is_db_ready()}
    return {"state": state.value}


@router.post("/initialize")
def initialize(body: InitializeRequest):
    """
    Perform first-run initialization: derive a key from the passphrase,
    create the encrypted DB, and return the one-time BIP39 recovery phrase.
    Returns 409 if already initialized.
    """
    if setup_service.get_state() == SetupState.INITIALIZED:
        raise conflict("Database is already initialized. Use /setup/unlock to load the key.")

    recovery_phrase = setup_service.initialize_db(body.passphrase)

    return {
        "state": SetupState.INITIALIZED.value,
        "recovery_phrase": recovery_phrase,
        "warning": "Save this phrase — it cannot be shown again",
    }


@router.post("/unlock")
def unlock(body: UnlockRequest):
    """
    Unlock an already-initialized DB after an app restart.
    Returns 400 if the DB has never been initialized.
    Returns 401 if the passphrase is wrong.
    """
    state = setup_service.get_state()

    if state == SetupState.UNINITIALIZED:
        raise bad_request("Not initialized yet. Call /setup/initialize first.")

    if setup_service.is_db_ready():
        return {"state": SetupState.INITIALIZED.value, "db_ready": True}

    success = setup_service.unlock_db(body.passphrase)
    if not success:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid passphrase")

    return {"state": SetupState.INITIALIZED.value, "db_ready": True}


@router.post("/recover")
def recover(body: RecoverRequest):
    """
    Recover DB access using the BIP39 recovery phrase and set a new passphrase.
    Returns 400 if the recovery phrase is invalid.
    """
    try:
        new_phrase = setup_service.recover_db(body.recovery_phrase, body.new_passphrase)
    except ValueError as exc:
        raise bad_request(str(exc))

    return {
        "state": SetupState.INITIALIZED.value,
        "new_recovery_phrase": new_phrase,
        "warning": "Save this new phrase — it cannot be shown again",
    }
