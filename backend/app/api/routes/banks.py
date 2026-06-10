from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import ContainerDep, SessionDep, UserDep
from app.application.bank_sync_service import BankSyncService, BankConnectionReader
from app.application.bank_connection_service import BankService as BankConnectionService
from app.schemas.bank import BankConnectionCreate, BankConnectionRead, BankConnectionUpdate

router = APIRouter(prefix="/api/banks", tags=["banks"])


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
    container: ContainerDep,
    session: SessionDep,
    user: UserDep,
):
    svc: BankConnectionService = container.bank_connection_service(session)
    return [_to_read(c) for c in svc.list_connections(user.id)]


@router.post("", status_code=201)
def create_connection(
    container: ContainerDep,
    session: SessionDep,
    body: BankConnectionCreate,
    user: UserDep,
):
    svc: BankConnectionService = container.bank_connection_service(session)
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
    container: ContainerDep,
    session: SessionDep,
    conn_id: int,
    user: UserDep,
):
    svc: BankConnectionService = container.bank_connection_service(session)
    conn = svc.get_connection(conn_id, user.id)
    if conn is None:
        raise HTTPException(status_code=404, detail="not found")
    return _to_read(conn)


@router.put("/{conn_id}")
def update_connection(
    container: ContainerDep,
    session: SessionDep,
    conn_id: int,
    body: BankConnectionUpdate,
    user: UserDep,
):
    svc: BankConnectionService = container.bank_connection_service(session)
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
    container: ContainerDep,
    session: SessionDep,
    conn_id: int,
    user: UserDep,
):
    svc: BankConnectionService = container.bank_connection_service(session)
    ok = svc.delete_connection(conn_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="not found")
    return {"ok": True}


@router.post("/{conn_id}/sync")
async def sync_connection(
    container: ContainerDep,
    session: SessionDep,
    conn_id: int,
    user: UserDep,
):
    bank_svc: BankConnectionService = container.bank_connection_service(session)
    sync_svc: BankSyncService = container.bank_sync_service(session)
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

    result = await sync_svc.sync_connection(reader)
    return {"imported": result.imported, "skipped": result.skipped, "total": result.total}
