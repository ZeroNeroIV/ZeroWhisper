import asyncio
import logging
from datetime import datetime

from sqlmodel import Session, select

from app.api.container import Container
from app.application.bank_sync_service import BankSyncService, BankConnectionReader
from app.infrastructure.database import DatabaseManager
from app.models.bank import BankConnection

logger = logging.getLogger(__name__)


async def _auto_sync_all_banks(db_manager: DatabaseManager, container: Container) -> None:
    if db_manager.engine is None:
        logger.info("Bank sync: database not initialized yet, skipping.")
        return

    with Session(db_manager.engine) as session:
        statement = select(BankConnection).where(BankConnection.is_active == True)
        connections = list(session.exec(statement).all())

    if not connections:
        return

    for conn in connections:
        try:
            reader = BankConnectionReader({
                "id": conn.id,
                "user_id": conn.user_id,
                "bank_name": conn.bank_name,
                "auth_type": conn.auth_type,
                "credentials": conn.credentials,
                "last_sync_at": conn.last_sync_at,
            })

            with Session(db_manager.engine) as session:
                svc = BankSyncService(
                    container.transaction_service(session),
                    container.category_repo(session),
                )
                result = await svc.sync_connection(reader)

                if result.imported or result.skipped:
                    logger.info(
                        "Bank sync [%s/%s]: %d imported, %d skipped",
                        conn.bank_name, conn.account_number,
                        result.imported, result.skipped,
                    )

                conn.last_sync_at = datetime.utcnow()
                session.add(conn)
                session.commit()
        except Exception as exc:
            logger.warning("Bank sync failed for connection %d: %s", conn.id, exc)


async def _sync_loop(db_manager: DatabaseManager, container: Container) -> None:
    while True:
        try:
            await _auto_sync_all_banks(db_manager, container)
        except Exception as exc:
            logger.warning("Bank sync loop error: %s", exc)
        await asyncio.sleep(3600)


def start_bank_sync_scheduler(db_manager: DatabaseManager, container: Container) -> asyncio.Task:
    loop = asyncio.get_event_loop()
    task = loop.create_task(_sync_loop(db_manager, container))
    return task
