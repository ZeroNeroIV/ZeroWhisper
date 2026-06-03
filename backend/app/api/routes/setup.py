"""Setup router — vault management, initialization, unlock, recovery."""
from fastapi import APIRouter, Depends, HTTPException, Request, status as http_status
from pydantic import BaseModel, Field

from app.core.exceptions import ValidationError, ConflictError, NotFoundError
from app.core.ratelimit import setup_rate_limit

router = APIRouter()


def _vm(request: Request):
    return request.app.state.container.vault_manager


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


class CreateOpenVaultRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)


class UnlockVaultRequest(BaseModel):
    passphrase: str | None = Field(default=None)


class RecoverVaultRequest(BaseModel):
    recovery_phrase: str = Field(...)
    new_passphrase: str = Field(..., min_length=8)


@router.get("/status")
def get_status(request: Request):
    vm = _vm(request)
    state = vm.get_state()
    if state == "INITIALIZED":
        return {
            "state": state,
            "db_ready": vm.is_db_ready(),
            "active_vault_id": vm.get_active_vault_id(),
        }
    return {"state": state}


@router.post("/initialize")
def initialize(
    request: Request,
    body: InitializeRequest,
    _: None = Depends(setup_rate_limit),
):
    vm = _vm(request)
    if vm.get_state() == "INITIALIZED":
        raise ConflictError("Already initialized. Use /setup/vaults to manage vaults.")
    recovery_phrase = vm.initialize(body.passphrase)
    return {
        "state": "INITIALIZED",
        "recovery_phrase": recovery_phrase,
        "warning": "Save this phrase — it cannot be shown again",
    }


@router.post("/unlock")
def unlock(
    request: Request,
    body: UnlockRequest,
    _: None = Depends(setup_rate_limit),
):
    vm = _vm(request)
    state = vm.get_state()
    if state == "UNINITIALIZED":
        raise ValidationError("Not initialized yet. Call /setup/initialize first.")
    if vm.is_db_ready():
        if not vm.verify_passphrase(body.passphrase):
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Invalid passphrase",
            )
        return {
            "state": "INITIALIZED",
            "db_ready": True,
            "active_vault_id": vm.get_active_vault_id(),
        }
    if not vm.unlock(body.passphrase):
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid passphrase",
        )
    return {
        "state": "INITIALIZED",
        "db_ready": True,
        "active_vault_id": vm.get_active_vault_id(),
    }


@router.post("/recover")
def recover(
    request: Request,
    body: RecoverRequest,
    _: None = Depends(setup_rate_limit),
):
    try:
        new_phrase = _vm(request).recover(body.recovery_phrase, body.new_passphrase)
    except ValueError as exc:
        raise ValidationError(str(exc))
    return {
        "state": "INITIALIZED",
        "new_recovery_phrase": new_phrase,
        "warning": "Save this new phrase — it cannot be shown again",
    }


@router.get("/vaults")
def list_vaults(request: Request):
    return {"vaults": _vm(request).list_vaults()}


@router.post("/vaults")
def create_vault(
    request: Request,
    body: CreateVaultRequest,
    _: None = Depends(setup_rate_limit),
):
    vault_id, recovery_phrase = _vm(request).create_vault(body.name, body.passphrase)
    return {
        "vault_id": vault_id,
        "recovery_phrase": recovery_phrase,
        "warning": "Save this phrase — it cannot be shown again",
    }


@router.post("/vaults/open")
def create_open_vault(request: Request, body: CreateOpenVaultRequest):
    vault_id = _vm(request).create_open_vault(body.name)
    return {"vault_id": vault_id}


@router.post("/vaults/{vault_id}/unlock")
def unlock_vault(
    request: Request,
    vault_id: str,
    body: UnlockVaultRequest,
    _: None = Depends(setup_rate_limit),
):
    vm = _vm(request)
    vault = vm.get_vault(vault_id)
    if not vault:
        raise NotFoundError("Vault", vault_id)
    if vault.get("vault_type") == "open":
        if vm.get_active_vault_id() == vault_id and vm.is_db_ready():
            return {"vault_id": vault_id, "db_ready": True}
        if not vm.unlock_open_vault(vault_id):
            raise HTTPException(status_code=500, detail="Failed to open vault")
        return {"vault_id": vault_id, "db_ready": True}
    if not body.passphrase:
        raise ValidationError("Passphrase required for secure vault")
    if vm.get_active_vault_id() == vault_id and vm.is_db_ready():
        if not vm.verify_passphrase(body.passphrase):
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Invalid passphrase",
            )
        return {"vault_id": vault_id, "db_ready": True}
    if not vm.unlock_vault(vault_id, body.passphrase):
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid passphrase",
        )
    return {"vault_id": vault_id, "db_ready": True}


@router.post("/vaults/{vault_id}/recover")
def recover_vault(
    request: Request,
    vault_id: str,
    body: RecoverVaultRequest,
    _: None = Depends(setup_rate_limit),
):
    vm = _vm(request)
    if not vm.get_vault(vault_id):
        raise NotFoundError("Vault", vault_id)
    try:
        new_phrase = vm.recover_vault(
            vault_id, body.recovery_phrase.strip(), body.new_passphrase
        )
    except ValueError as exc:
        raise ValidationError(str(exc))
    return {
        "vault_id": vault_id,
        "new_recovery_phrase": new_phrase,
        "warning": "Save this new phrase — it cannot be shown again",
    }
