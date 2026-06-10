"""
Whisper use case — natural language → financial action → confirmation.

The agent classifies a message into an intent:
- record_expense / record_income → confirmable transaction proposal
- transfer                       → confirmable wallet-to-wallet transfer proposal
- query_balance / query_spending → answered immediately from local data
- unknown                        → clarification reply

Proposals live in a ProposalStore owned by the DI container (one per
process), because services are constructed per request — a store on the
service instance would forget every proposal as soon as the request ended.
"""
from __future__ import annotations

import threading
from datetime import date, timedelta
from app.core.time import utc_now
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.domain.transaction import (
    BASE_CURRENCY,
    SOURCE_WHISPER,
    Transaction as DomainTransaction,
)
from app.core.domain.wallet import Wallet
from app.core.exceptions import NotFoundError, ValidationError
from app.core.ports.ai_provider import AIProvider
from app.core.ports.category_repo import CategoryRepository
from app.core.ports.transaction_repo import TransactionRepository
from app.application.transaction_service import TransactionService
from app.application.wallet_service import WalletService

FALLBACK_CATEGORY = "Other"


class PendingProposal:
    __slots__ = ("proposal_data", "user_id", "created_at")

    def __init__(self, proposal_data: dict, user_id: str) -> None:
        self.proposal_data = proposal_data
        self.user_id = user_id
        self.created_at = utc_now()


class ProposalStore:
    """In-memory pending-proposal store shared across requests, with TTL expiry.

    Guarded by a lock because FastAPI serves sync endpoints from a threadpool,
    so puts/gets/cleanups can run concurrently. Proposals do not survive a
    process restart — acceptable for short-lived confirmations.
    """

    def __init__(self, ttl_minutes: int = settings.whisper_proposal_ttl_minutes) -> None:
        self._ttl = timedelta(minutes=ttl_minutes)
        self._pending: dict[str, PendingProposal] = {}
        self._lock = threading.Lock()

    def put(self, proposal_data: dict, user_id: UUID) -> str:
        proposal_id = str(uuid4())
        with self._lock:
            self._cleanup_expired()
            self._pending[proposal_id] = PendingProposal(proposal_data, str(user_id))
        return proposal_id

    def get(self, proposal_id: str, user_id: UUID) -> dict | None:
        with self._lock:
            self._cleanup_expired()
            entry = self._pending.get(proposal_id)
            if not entry or entry.user_id != str(user_id):
                return None
            return entry.proposal_data

    def remove(self, proposal_id: str) -> None:
        with self._lock:
            self._pending.pop(proposal_id, None)

    def _cleanup_expired(self) -> None:
        cutoff = utc_now() - self._ttl
        expired = [pid for pid, p in self._pending.items() if p.created_at < cutoff]
        for pid in expired:
            del self._pending[pid]


class WhisperService:

    def __init__(
        self,
        tx_service: TransactionService,
        tx_repo: TransactionRepository,
        cat_repo: CategoryRepository,
        wallet_service: WalletService,
        ai_provider: AIProvider,
        proposal_store: ProposalStore,
    ) -> None:
        self._tx_service = tx_service
        self._tx_repo = tx_repo
        self._cat_repo = cat_repo
        self._wallets = wallet_service
        self._ai = ai_provider
        self._store = proposal_store

    # ── Parsing ───────────────────────────────────────────────────────────────────

    async def parse_message(self, user_id: UUID, message: str) -> dict:
        categories = self._cat_repo.find_by_user(user_id)
        cat_context = [
            {"name": c.name, "type": c.type.value}
            for c in categories if c.type.value != "transfer"
        ]
        wallets = self._wallets.list_wallets(user_id)
        wallet_context = [
            {"name": w.name, "type": w.type.value, "currency": w.currency}
            for w in wallets
        ]

        action = await self._ai.extract_action(message, cat_context, wallet_context)
        intent = action.get("intent", "unknown")

        if intent in ("record_expense", "record_income"):
            return await self._propose_transaction(user_id, intent, action, wallets)
        if intent == "transfer":
            return self._propose_transfer(user_id, action, wallets)
        if intent == "query_balance":
            return self._answer_balance(action, wallets)
        if intent == "query_spending":
            return self._answer_spending(user_id)
        return self._clarify(action)

    async def _propose_transaction(
        self, user_id: UUID, intent: str, action: dict, wallets: list[Wallet],
    ) -> dict:
        if not action.get("amount") or action["amount"] <= 0:
            return self._clarify(action, fallback="How much was it?")

        category = action.get("category") or FALLBACK_CATEGORY
        if not self._cat_repo.find_by_name(user_id, category):
            category = FALLBACK_CATEGORY
        wallet = _match_wallet(action.get("wallet"), wallets)

        proposal = {
            "kind": "transaction",
            "intent": intent,
            "amount_original": str(action["amount"]),
            "currency_original": action.get("currency") or BASE_CURRENCY,
            "category": category,
            "description": action.get("description"),
            "transaction_date": action.get("transaction_date"),
            "wallet_id": str(wallet.id) if wallet else None,
            "wallet_name": wallet.name if wallet else None,
            "confidence": action.get("confidence", 0.0),
        }
        proposal_id = self._store.put(proposal, user_id)

        now = utc_now()
        spending = self._tx_repo.monthly_spending_by_category(user_id, now.year, now.month)
        this_month_total = spending.get(category, Decimal("0"))
        transaction_count = self._tx_repo.count_by_category_month(
            user_id, category, now.year, now.month,
        )
        persona = await self._ai.generate_persona(
            category, float(this_month_total), transaction_count,
        )

        return {
            "action": "proposal",
            "proposal_id": proposal_id,
            "proposal": proposal,
            "persona_message": persona,
            "spending_context": {
                "category": category,
                "this_month_total": str(this_month_total),
                "transaction_count": transaction_count,
            },
        }

    def _propose_transfer(self, user_id: UUID, action: dict, wallets: list[Wallet]) -> dict:
        if len(wallets) < 2:
            return self._reply("You need at least two wallets to make a transfer. Create one on the Wallets page first.")
        if not action.get("amount") or action["amount"] <= 0:
            return self._clarify(action, fallback="How much do you want to transfer?")

        from_wallet = _match_wallet(action.get("from_wallet"), wallets)
        to_wallet = _match_wallet(action.get("to_wallet"), wallets)
        if not from_wallet or not to_wallet:
            names = ", ".join(w.name for w in wallets)
            return self._reply(f"Which wallets should I move the money between? You have: {names}.")
        if from_wallet.id == to_wallet.id:
            return self._reply("The source and destination wallets are the same — which one should the money go to?")

        proposal = {
            "kind": "transfer",
            "intent": "transfer",
            "amount_original": str(action["amount"]),
            "currency_original": action.get("currency") or from_wallet.currency,
            "from_wallet_id": str(from_wallet.id),
            "from_wallet_name": from_wallet.name,
            "to_wallet_id": str(to_wallet.id),
            "to_wallet_name": to_wallet.name,
            "description": action.get("description"),
            "transaction_date": action.get("transaction_date"),
            "confidence": action.get("confidence", 0.0),
        }
        proposal_id = self._store.put(proposal, user_id)
        return {
            "action": "proposal",
            "proposal_id": proposal_id,
            "proposal": proposal,
            "persona_message": (
                f"Moving {proposal['amount_original']} {proposal['currency_original']} "
                f"from {from_wallet.name} to {to_wallet.name} — confirm?"
            ),
            "spending_context": None,
        }

    def _answer_balance(self, action: dict, wallets: list[Wallet]) -> dict:
        if not wallets:
            return self._reply("You don't have any wallets yet. Create one on the Wallets page to start tracking balances.")
        wallet = _match_wallet(action.get("wallet"), wallets)
        if wallet:
            return self._reply(
                f"{wallet.name} holds {wallet.balance:.2f} JOD.",
                data={"wallets": [_wallet_summary(wallet)]},
            )
        total = sum((w.balance for w in wallets), Decimal("0"))
        lines = "; ".join(f"{w.name}: {w.balance:.2f}" for w in wallets)
        return self._reply(
            f"Across your {len(wallets)} wallets you have {total:.2f} JOD ({lines}).",
            data={"wallets": [_wallet_summary(w) for w in wallets]},
        )

    def _answer_spending(self, user_id: UUID) -> dict:
        now = utc_now()
        expenses = self._tx_repo.monthly_spending_by_category(
            user_id, now.year, now.month, types=["expense"],
        )
        if not expenses:
            return self._reply("No spending recorded this month. Either impressive discipline or an empty ledger.")
        total = sum(expenses.values(), Decimal("0"))
        top = sorted(expenses.items(), key=lambda kv: kv[1], reverse=True)[:5]
        lines = "; ".join(f"{cat}: {amt:.2f}" for cat, amt in top)
        return self._reply(
            f"This month you've spent {total:.2f} JOD. Top categories — {lines}.",
            data={"spending": [{"category": c, "total_jod": str(a)} for c, a in top]},
        )

    def _clarify(self, action: dict, fallback: str = "I didn't catch that — what would you like me to do?") -> dict:
        return self._reply(action.get("reply") or fallback)

    @staticmethod
    def _reply(message: str, data: dict | None = None) -> dict:
        return {
            "action": "reply",
            "proposal_id": None,
            "proposal": None,
            "persona_message": message,
            "spending_context": None,
            "data": data,
        }

    # ── Confirmation ──────────────────────────────────────────────────────────────

    # Fields the client may adjust before confirming. Structural fields
    # (kind, intent) and identity fields stay server-controlled.
    _TX_OVERRIDABLE = frozenset({
        "amount_original", "currency_original", "category",
        "description", "transaction_date", "wallet_id",
    })
    _TRANSFER_OVERRIDABLE = frozenset({
        "amount_original", "currency_original", "description",
        "transaction_date", "from_wallet_id", "to_wallet_id",
    })

    def confirm(self, proposal_id: str, user_id: UUID, overrides: dict | None = None) -> DomainTransaction:
        proposal = self._store.get(proposal_id, user_id)
        if proposal is None:
            raise NotFoundError("Proposal", proposal_id)

        allowed = (
            self._TRANSFER_OVERRIDABLE if proposal["kind"] == "transfer"
            else self._TX_OVERRIDABLE
        )
        safe_overrides = {k: v for k, v in (overrides or {}).items() if k in allowed}
        merged = {**proposal, **safe_overrides}
        tx_date = _parse_date(merged.get("transaction_date"))
        amount = _parse_amount(merged.get("amount_original"))

        if proposal["kind"] == "transfer":
            out_leg, _ = self._tx_service.transfer(
                user_id=user_id,
                from_wallet_id=UUID(str(merged["from_wallet_id"])),
                to_wallet_id=UUID(str(merged["to_wallet_id"])),
                amount_original=amount,
                currency_original=merged["currency_original"],
                transaction_date=tx_date,
                description=merged.get("description"),
                source=SOURCE_WHISPER,
            )
            tx = out_leg
        else:
            wallet_id = merged.get("wallet_id")
            tx = self._tx_service.create(
                user_id=user_id,
                amount_original=amount,
                currency_original=merged["currency_original"],
                category=merged["category"],
                transaction_date=tx_date,
                description=merged.get("description"),
                source=SOURCE_WHISPER,
                wallet_id=UUID(str(wallet_id)) if wallet_id else None,
            )
        self._store.remove(proposal_id)
        return tx

    def reject(self, proposal_id: str, user_id: UUID) -> bool:
        if self._store.get(proposal_id, user_id) is None:
            return False
        self._store.remove(proposal_id)
        return True

    def get_ai_provider(self) -> AIProvider:
        return self._ai


def _match_wallet(name: str | None, wallets: list[Wallet]) -> Wallet | None:
    """Resolve a model-suggested wallet name against the user's wallets."""
    if not name:
        return None
    needle = name.strip().lower()
    for w in wallets:
        if w.name.lower() == needle:
            return w
    for w in wallets:
        if needle in w.name.lower() or w.name.lower() in needle:
            return w
    return None


def _wallet_summary(w: Wallet) -> dict:
    return {
        "id": str(w.id),
        "name": w.name,
        "type": w.type.value,
        "currency": w.currency,
        "balance": str(w.balance),
    }


def _parse_date(value) -> date:
    if isinstance(value, date):
        return value
    if value:
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            pass
    return utc_now().date()


def _parse_amount(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValidationError(f"Invalid amount '{value}'")
    if amount <= 0:
        raise ValidationError("Amount must be positive")
    return amount
