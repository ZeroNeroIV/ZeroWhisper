from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid4, UUID

from sqlmodel import Session, select, func

from app.models.transaction import Transaction
from app.schemas.agent import TransactionProposal, SpendingContext, WhisperResponse
from app.schemas.transaction import TransactionCreate
from app.services.openai_service import extract_transaction, generate_persona
from app.services.transactions import create_transaction

_PROPOSAL_TTL = timedelta(minutes=15)

# proposal_id → (proposal, user_id, created_at)
_pending: dict[str, tuple[TransactionProposal, str, datetime]] = {}


async def parse_message(session: Session, user_id: str, message: str) -> WhisperResponse:
    proposal = await extract_transaction(message)

    now = datetime.utcnow()
    month_start = date(now.year, now.month, 1)

    row = session.exec(
        select(
            func.coalesce(func.sum(Transaction.amount_base), 0),
            func.count(Transaction.id),
        ).where(
            Transaction.user_id == UUID(user_id),
            Transaction.category == proposal.category,
            Transaction.transaction_date >= month_start,
            Transaction.is_deleted == False,
        )
    ).one()
    this_month_total = Decimal(str(row[0]))
    transaction_count = int(row[1])

    spending_ctx = SpendingContext(
        category=proposal.category,
        this_month_total=this_month_total,
        transaction_count=transaction_count,
    )

    persona = await generate_persona(
        proposal.category,
        {
            "category": proposal.category,
            "this_month_total": float(this_month_total),
            "transaction_count": transaction_count,
        },
    )

    proposal_id = str(uuid4())
    _pending[proposal_id] = (proposal, user_id, datetime.utcnow())

    return WhisperResponse(
        proposal_id=proposal_id,
        proposal=proposal,
        persona_message=persona,
        spending_context=spending_ctx,
    )


def _cleanup_expired() -> None:
    cutoff = datetime.utcnow() - _PROPOSAL_TTL
    expired = [pid for pid, (_, _, created_at) in _pending.items() if created_at < cutoff]
    for pid in expired:
        del _pending[pid]


def confirm_proposal(
    session: Session,
    proposal_id: str,
    user_id: str,
    overrides: dict | None = None,
) -> Transaction:
    _cleanup_expired()

    entry = _pending.get(proposal_id)
    if entry is None:
        raise ValueError("not found")

    proposal, stored_user_id, _ = entry
    if stored_user_id != user_id:
        raise ValueError("not found")

    overrides = overrides or {}
    tx_data = TransactionCreate(
        amount_original=overrides.get("amount_original", proposal.amount_original),
        currency_original=overrides.get("currency_original", proposal.currency_original),
        category=overrides.get("category", proposal.category),
        description=overrides.get("description", proposal.description),
        transaction_date=overrides.get("transaction_date", datetime.utcnow().date()),
    )

    tx = create_transaction(session, UUID(user_id), tx_data, source="whisper")
    del _pending[proposal_id]
    return tx


def reject_proposal(proposal_id: str, user_id: str) -> bool:
    entry = _pending.get(proposal_id)
    if entry is None:
        return False
    _, stored_user_id, _ = entry
    if stored_user_id != user_id:
        return False
    del _pending[proposal_id]
    return True
