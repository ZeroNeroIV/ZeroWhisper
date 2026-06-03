"""
Whisper use case — natural language → transaction proposal → confirmation.

Eliminates the in-memory module-level `_pending` dict and the inline
spending context queries from the old whisper_service.py. Now uses
repository interfaces and an AI provider strategy.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.domain.transaction import Transaction as DomainTransaction
from app.core.exceptions import NotFoundError, ValidationError
from app.core.ports.ai_provider import AIProvider
from app.core.ports.transaction_repo import TransactionRepository
from app.core.ports.category_repo import CategoryRepository
from app.application.transaction_service import TransactionService


class PendingProposal:
    __slots__ = ("proposal_data", "user_id", "created_at")

    def __init__(self, proposal_data: dict, user_id: str) -> None:
        self.proposal_data = proposal_data
        self.user_id = user_id
        self.created_at = datetime.utcnow()


class WhisperService:

    def __init__(
        self,
        tx_service: TransactionService,
        tx_repo: TransactionRepository,
        cat_repo: CategoryRepository,
        ai_provider: AIProvider,
        proposal_ttl_minutes: int = settings.whisper_proposal_ttl_minutes,
    ) -> None:
        self._tx_service = tx_service
        self._tx_repo = tx_repo
        self._cat_repo = cat_repo
        self._ai = ai_provider
        self._ttl = timedelta(minutes=proposal_ttl_minutes)
        self._pending: dict[str, PendingProposal] = {}

    async def parse_message(self, user_id: UUID, message: str) -> dict:
        user_cats = self._cat_repo.find_by_user(user_id)
        cat_names = [c.name for c in user_cats]

        proposal = await self._ai.extract_transaction(message, cat_names)

        now = datetime.utcnow()
        month_start = date(now.year, now.month, 1)

        spending = self._tx_repo.monthly_spending_by_category(
            user_id, now.year, now.month,
        )

        this_month_total = spending.get(proposal["category"], Decimal("0"))
        transaction_count = 0  # TODO: repo should expose count

        persona = await self._ai.generate_persona(
            proposal["category"],
            float(this_month_total),
            transaction_count,
        )

        proposal_id = str(uuid4())
        self._pending[proposal_id] = PendingProposal(proposal, str(user_id))

        return {
            "proposal_id": proposal_id,
            "proposal": proposal,
            "persona_message": persona,
            "spending_context": {
                "category": proposal["category"],
                "this_month_total": str(this_month_total),
                "transaction_count": transaction_count,
            },
        }

    def _cleanup_expired(self) -> None:
        cutoff = datetime.utcnow() - self._ttl
        expired = [pid for pid, p in self._pending.items() if p.created_at < cutoff]
        for pid in expired:
            del self._pending[pid]

    def confirm(self, proposal_id: str, user_id: UUID, overrides: dict | None = None) -> DomainTransaction:
        self._cleanup_expired()
        entry = self._pending.get(proposal_id)
        if not entry or entry.user_id != str(user_id):
            raise NotFoundError("Proposal", proposal_id)

        overrides = overrides or {}
        proposal = entry.proposal_data
        tx_date_str = proposal.get("transaction_date")
        tx_date = date.fromisoformat(tx_date_str) if tx_date_str else datetime.utcnow().date()

        tx = self._tx_service.create(
            user_id=user_id,
            amount_original=Decimal(str(overrides.get("amount_original", proposal["amount_original"]))),
            currency_original=overrides.get("currency_original", proposal["currency_original"]),
            category=overrides.get("category", proposal["category"]),
            transaction_date=overrides.get("transaction_date", tx_date),
            description=overrides.get("description", proposal.get("description")),
            source="whisper",
        )
        del self._pending[proposal_id]
        return tx

    def reject(self, proposal_id: str, user_id: UUID) -> bool:
        entry = self._pending.get(proposal_id)
        if not entry or entry.user_id != str(user_id):
            return False
        del self._pending[proposal_id]
        return True

    def get_ai_provider(self) -> AIProvider:
        return self._ai
