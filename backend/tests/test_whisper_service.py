from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.application.exchange_rate_service import ExchangeRateService
from app.application.transaction_service import TransactionService
from app.application.wallet_service import WalletService
from app.application.whisper_service import ProposalStore, WhisperService
from app.core.domain.category import Category, CategoryType
from app.core.domain.transaction import TransactionType
from app.core.domain.wallet import WalletType
from app.core.exceptions import NotFoundError
from app.core.ports.ai_provider import AIProvider
from tests.helpers import (
    InMemoryCategoryRepository,
    InMemoryTransactionRepository,
    InMemoryWalletRepository,
)


class FakeAIProvider(AIProvider):
    """Returns a canned action; records the context it was given."""

    def __init__(self, action: dict) -> None:
        self.action = action
        self.seen_categories: list[dict] | None = None
        self.seen_wallets: list[dict] | None = None

    async def extract_action(self, text: str, categories: list[dict], wallets: list[dict]) -> dict:
        self.seen_categories = categories
        self.seen_wallets = wallets
        return self.action

    async def generate_persona(self, category: str, this_month_total: float, transaction_count: int) -> str:
        return "Noted."


def _base_action(**overrides) -> dict:
    action = {
        "intent": "record_expense",
        "amount": 12.5,
        "currency": "JOD",
        "description": "lunch",
        "category": "Food",
        "wallet": None,
        "from_wallet": None,
        "to_wallet": None,
        "transaction_date": None,
        "confidence": 0.9,
        "reply": None,
    }
    action.update(overrides)
    return action


@pytest.fixture
def deps():
    uid = uuid4()
    tx_repo = InMemoryTransactionRepository()
    cat_repo = InMemoryCategoryRepository()
    wallet_repo = InMemoryWalletRepository()
    cat_repo.seed_defaults(uid)
    cat_repo.save(Category(uid, "Other", CategoryType.EXPENSE))
    rate_svc = Mock(spec=ExchangeRateService)
    rate_svc.get_rate.return_value = Decimal("0.709")
    tx_svc = TransactionService(tx_repo, cat_repo, rate_svc, wallet_repo)
    wallet_svc = WalletService(wallet_repo, tx_repo)
    return uid, tx_repo, cat_repo, wallet_svc, tx_svc


def make_service(deps, action: dict, store: ProposalStore | None = None) -> tuple[WhisperService, FakeAIProvider]:
    uid, tx_repo, cat_repo, wallet_svc, tx_svc = deps
    ai = FakeAIProvider(action)
    svc = WhisperService(tx_svc, tx_repo, cat_repo, wallet_svc, ai, store or ProposalStore())
    return svc, ai


class TestExpenseProposal:
    async def test_parse_then_confirm_creates_transaction(self, deps) -> None:
        uid = deps[0]
        store = ProposalStore()
        svc, _ = make_service(deps, _base_action(), store)

        result = await svc.parse_message(uid, "spent 12.5 on lunch")
        assert result["action"] == "proposal"
        assert result["proposal"]["category"] == "Food"

        # A different service instance sharing the store can confirm —
        # this is the regression test for per-request proposal loss.
        svc2, _ = make_service(deps, _base_action(), store)
        tx = svc2.confirm(result["proposal_id"], uid)
        assert tx.amount_original == Decimal("12.5")
        assert tx.source == "whisper"
        assert tx.type == TransactionType.EXPENSE

    async def test_confirm_applies_overrides(self, deps) -> None:
        uid = deps[0]
        svc, _ = make_service(deps, _base_action())
        result = await svc.parse_message(uid, "spent 12.5 on lunch")
        tx = svc.confirm(result["proposal_id"], uid, overrides={"amount_original": "20"})
        assert tx.amount_original == Decimal("20")

    async def test_unknown_category_falls_back_to_other(self, deps) -> None:
        uid = deps[0]
        svc, _ = make_service(deps, _base_action(category="Nonsense"))
        result = await svc.parse_message(uid, "spent 12.5 on stuff")
        assert result["proposal"]["category"] == "Other"

    async def test_wallet_resolved_by_name(self, deps) -> None:
        uid, _, _, wallet_svc, _ = deps
        w = wallet_svc.create(uid, "Cash", type=WalletType.CASH)
        svc, _ = make_service(deps, _base_action(wallet="cash"))
        result = await svc.parse_message(uid, "spent 12.5 on lunch from cash")
        assert result["proposal"]["wallet_id"] == str(w.id)

    def test_confirm_unknown_proposal_raises(self, deps) -> None:
        uid = deps[0]
        svc, _ = make_service(deps, _base_action())
        with pytest.raises(NotFoundError):
            svc.confirm(str(uuid4()), uid)

    async def test_reject_discards(self, deps) -> None:
        uid = deps[0]
        svc, _ = make_service(deps, _base_action())
        result = await svc.parse_message(uid, "spent 12.5")
        assert svc.reject(result["proposal_id"], uid) is True
        assert svc.reject(result["proposal_id"], uid) is False


class TestTransferProposal:
    async def test_transfer_flow(self, deps) -> None:
        uid, _, _, wallet_svc, _ = deps
        src = wallet_svc.create(uid, "Family Savings", type=WalletType.SAVINGS,
                                initial_balance=Decimal("1000"))
        dst = wallet_svc.create(uid, "Held Money", type=WalletType.CASH)
        action = _base_action(
            intent="transfer", amount=200,
            from_wallet="Family Savings", to_wallet="Held Money",
        )
        svc, _ = make_service(deps, action)
        result = await svc.parse_message(uid, "move 200 from family savings to held money")
        assert result["action"] == "proposal"
        assert result["proposal"]["kind"] == "transfer"

        tx = svc.confirm(result["proposal_id"], uid)
        assert tx.type == TransactionType.TRANSFER_OUT
        assert wallet_svc.get_wallet(src.id, uid).balance == Decimal("800")
        assert wallet_svc.get_wallet(dst.id, uid).balance == Decimal("200")

    async def test_asks_when_wallets_unresolved(self, deps) -> None:
        uid, _, _, wallet_svc, _ = deps
        wallet_svc.create(uid, "A")
        wallet_svc.create(uid, "B")
        action = _base_action(intent="transfer", amount=200, from_wallet="X", to_wallet=None)
        svc, _ = make_service(deps, action)
        result = await svc.parse_message(uid, "move 200")
        assert result["action"] == "reply"
        assert result["proposal_id"] is None

    async def test_requires_two_wallets(self, deps) -> None:
        uid = deps[0]
        action = _base_action(intent="transfer", amount=200)
        svc, _ = make_service(deps, action)
        result = await svc.parse_message(uid, "move 200")
        assert result["action"] == "reply"


class TestQueries:
    async def test_balance_query(self, deps) -> None:
        uid, _, _, wallet_svc, _ = deps
        wallet_svc.create(uid, "Cash", initial_balance=Decimal("75"))
        svc, _ = make_service(deps, _base_action(intent="query_balance", wallet="Cash"))
        result = await svc.parse_message(uid, "how much in cash?")
        assert result["action"] == "reply"
        assert "75.00" in result["persona_message"]

    async def test_spending_query(self, deps) -> None:
        uid, _, cat_repo, _, tx_svc = deps
        tx_svc.create(uid, Decimal("80"), "JOD", "Food", date.today())
        svc, _ = make_service(deps, _base_action(intent="query_spending"))
        result = await svc.parse_message(uid, "what did I spend this month?")
        assert result["action"] == "reply"
        assert "80.00" in result["persona_message"]

    async def test_unknown_uses_model_reply(self, deps) -> None:
        uid = deps[0]
        svc, _ = make_service(deps, _base_action(intent="unknown", reply="Could you rephrase?"))
        result = await svc.parse_message(uid, "asdf")
        assert result["persona_message"] == "Could you rephrase?"


class TestContextGrounding:
    async def test_wallets_and_categories_passed_to_model(self, deps) -> None:
        uid, _, _, wallet_svc, _ = deps
        wallet_svc.create(uid, "Cash", type=WalletType.CASH)
        svc, ai = make_service(deps, _base_action())
        await svc.parse_message(uid, "spent 5")
        assert any(w["name"] == "Cash" for w in ai.seen_wallets)
        assert any(c["name"] == "Food" for c in ai.seen_categories)
        # The reserved transfer category is internal — never offered to the model
        assert all(c["type"] != "transfer" for c in ai.seen_categories)


class TestProposalStore:
    def test_expires_old_proposals(self) -> None:
        from datetime import datetime, timedelta
        store = ProposalStore(ttl_minutes=10)
        uid = uuid4()
        pid = store.put({"kind": "transaction"}, uid)
        store._pending[pid].created_at = datetime.utcnow() - timedelta(minutes=11)
        assert store.get(pid, uid) is None

    def test_scoped_to_user(self) -> None:
        store = ProposalStore()
        pid = store.put({"kind": "transaction"}, uuid4())
        assert store.get(pid, uuid4()) is None
