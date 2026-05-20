"""
Setup router — handles vault management, initialization, unlock, and recovery.

All endpoints here are exempt from SetupGuardMiddleware so they are reachable
before (and during) the setup flow.
"""
from fastapi import APIRouter, HTTPException, status as http_status
from pydantic import BaseModel, Field

from app.exceptions import bad_request, conflict, not_found
from app.services import setup as setup_service
from app.services.setup import SetupState

router = APIRouter()


# ── Request / response schemas ──────────────────────────────────────────────────

class InitializeRequest(BaseModel):
    passphrase: str = Field(..., min_length=8)


class UnlockRequest(BaseModel):
    passphrase: str = Field(...)


class RecoverRequest(BaseModel):
    recovery_phrase: str = Field(...)
    new_passphrase: str = Field(..., min_length=8)


class CreateVaultRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    passphrase: str = Field(..., min_length=8)


class UnlockVaultRequest(BaseModel):
    passphrase: str = Field(...)


class RecoverVaultRequest(BaseModel):
    recovery_phrase: str = Field(...)
    new_passphrase: str = Field(..., min_length=8)


# ── Legacy single-vault endpoints (backward-compat) ─────────────────────────────

@router.get("/status")
def get_status():
    """Return the current setup state and active vault info."""
    state = setup_service.get_state()
    if state == SetupState.INITIALIZED:
        return {
            "state": state.value,
            "db_ready": setup_service.is_db_ready(),
            "active_vault_id": setup_service.get_active_vault_id(),
        }
    return {"state": state.value}


@router.post("/initialize")
def initialize(body: InitializeRequest):
    """
    First-run initialization: create the 'Default' vault.
    Returns 409 if a vault already exists.
    """
    if setup_service.get_state() == SetupState.INITIALIZED:
        raise conflict("Already initialized. Use /setup/vaults to manage vaults.")

    recovery_phrase = setup_service.initialize_db(body.passphrase)
    return {
        "state": SetupState.INITIALIZED.value,
        "recovery_phrase": recovery_phrase,
        "warning": "Save this phrase — it cannot be shown again",
    }


@router.post("/unlock")
def unlock(body: UnlockRequest):
    """
    Unlock the first registered vault (backward-compat).
    Returns 401 if the passphrase is wrong.
    """
    state = setup_service.get_state()
    if state == SetupState.UNINITIALIZED:
        raise bad_request("Not initialized yet. Call /setup/initialize first.")

    if setup_service.is_db_ready():
        if not setup_service.verify_passphrase(body.passphrase):
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Invalid passphrase",
            )
        return {
            "state": SetupState.INITIALIZED.value,
            "db_ready": True,
            "active_vault_id": setup_service.get_active_vault_id(),
        }

    if not setup_service.unlock_db(body.passphrase):
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid passphrase",
        )
    return {
        "state": SetupState.INITIALIZED.value,
        "db_ready": True,
        "active_vault_id": setup_service.get_active_vault_id(),
    }


@router.post("/recover")
def recover(body: RecoverRequest):
    """Recover the first registered vault (backward-compat)."""
    try:
        new_phrase = setup_service.recover_db(body.recovery_phrase, body.new_passphrase)
    except ValueError as exc:
        raise bad_request(str(exc))
    return {
        "state": SetupState.INITIALIZED.value,
        "new_recovery_phrase": new_phrase,
        "warning": "Save this new phrase — it cannot be shown again",
    }


# ── Multi-vault endpoints ───────────────────────────────────────────────────────

@router.get("/vaults")
def list_vaults():
    """Return all registered vaults with metadata and active status."""
    return {"vaults": setup_service.list_vaults()}


@router.post("/vaults")
def create_vault(body: CreateVaultRequest):
    """
    Create a new encrypted vault and activate it immediately.
    Returns the one-time BIP39 recovery phrase.
    """
    vault_id, recovery_phrase = setup_service.create_vault(body.name, body.passphrase)
    return {
        "vault_id": vault_id,
        "recovery_phrase": recovery_phrase,
        "warning": "Save this phrase — it cannot be shown again",
    }


@router.post("/vaults/{vault_id}/unlock")
def unlock_vault(vault_id: str, body: UnlockVaultRequest):
    """
    Unlock a specific vault and make it active.
    Returns 404 if the vault does not exist, 401 if the passphrase is wrong.
    """
    if not setup_service.get_vault(vault_id):
        raise not_found("Vault not found")

    if setup_service.get_active_vault_id() == vault_id and setup_service.is_db_ready():
        if not setup_service.verify_passphrase(body.passphrase):
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Invalid passphrase",
            )
        return {"vault_id": vault_id, "db_ready": True}

    if not setup_service.unlock_vault(vault_id, body.passphrase):
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid passphrase",
        )
    return {"vault_id": vault_id, "db_ready": True}


@router.post("/vaults/{vault_id}/recover")
def recover_vault(vault_id: str, body: RecoverVaultRequest):
    """
    Recover a specific vault using its BIP39 recovery phrase and set a new passphrase.
    Returns 404 if the vault does not exist, 400 if the recovery phrase is invalid.
    """
    if not setup_service.get_vault(vault_id):
        raise not_found("Vault not found")
    try:
        new_phrase = setup_service.recover_vault(
            vault_id, body.recovery_phrase.strip(), body.new_passphrase
        )
    except ValueError as exc:
        raise bad_request(str(exc))
    return {
        "vault_id": vault_id,
        "new_recovery_phrase": new_phrase,
        "warning": "Save this new phrase — it cannot be shown again",
    }
