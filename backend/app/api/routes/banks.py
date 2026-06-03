"""Bank connection routes — CRUD + sync using new Hexagonal services."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from app.api.deps import get_current_user, get_session, _get_bank_sync_service
from app.application.bank_sync_service import BankSyncService, BankConnectionReader
from app.application.bank_connection_service import BankService as BankConnectionService
from app.core.domain.user import User
from app.schemas.bank import BankConnectionCreate, BankConnectionRead, BankConnectionUpdate

router = APIRouter(prefix="/api/banks", tags=["banks"])


def _get_svc(request: Request, session: Session = Depends(get_session)) -> BankConnectionService:
    return request.app.state.container.bank_connection_service(session)


def _to_read(conn) -> BankConnectionRead:
    return BankConnectionRead(
        id=conn.id,
        bank_name=conn.bank_name,
        auth_type=conn.auth_type,
        account_number=conn.account_number,
        is_active=conn.is_active,
        last_sync_at=conn.last_sync_at,
        created_at=conn.created_at,
    )


@router.get("")
def list_connections(
    request: Request,
    user: User = Depends(get_current_user),
    svc=Depends(_get_svc),
):
    return [_to_read(c) for c in svc.list_connections(user.id)]


@router.post("", status_code=201)
def create_connection(
    body: BankConnectionCreate,
    request: Request,
    user: User = Depends(get_current_user),
    svc=Depends(_get_svc),
):
    conn = svc.create_connection(
        user_id=user.id,
        bank_name=body.bank_name,
        auth_type=body.auth_type,
        account_number=body.account_number,
        credentials=body.credentials,
    )
    return _to_read(conn)


@router.get("/{conn_id}")
def get_connection(
    conn_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    svc=Depends(_get_svc),
):
    conn = svc.get_connection(conn_id, user.id)
    if conn is None:
        raise HTTPException(status_code=404, detail="not found")
    return _to_read(conn)


@router.put("/{conn_id}")
def update_connection(
    conn_id: int,
    body: BankConnectionUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    svc=Depends(_get_svc),
):
    conn = svc.update_connection(
        conn_id, user.id,
        is_active=body.is_active,
        credentials=body.credentials,
        account_number=body.account_number,
    )
    if conn is None:
        raise HTTPException(status_code=404, detail="not found")
    return _to_read(conn)


@router.delete("/{conn_id}")
def delete_connection(
    conn_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    svc=Depends(_get_svc),
):
    ok = svc.delete_connection(conn_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="not found")
    return {"ok": True}


@router.post("/{conn_id}/sync")
async def sync_connection(
    conn_id: int,
    request: Request,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
    svc: BankSyncService = Depends(_get_bank_sync_service),
    bank_svc=Depends(_get_svc),
):
    conn = bank_svc.get_connection(conn_id, user.id)
    if conn is None:
        raise HTTPException(status_code=404, detail="not found")

    reader = BankConnectionReader({
        "id": conn.id,
        "user_id": conn.user_id,
        "bank_name": conn.bank_name,
        "auth_type": conn.auth_type,
        "credentials": conn.credentials,
        "last_sync_at": conn.last_sync_at,
    })

    result = await svc.sync_connection(reader)
    return {"imported": result.imported, "skipped": result.skipped, "total": result.total}
