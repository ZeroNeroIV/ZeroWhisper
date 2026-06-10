from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.application.exchange_rate_service import ExchangeRateService
from app.application.transaction_service import TransactionService
from app.application.wallet_service import WalletService
from app.core.domain.category import Category, CategoryType
from app.core.domain.transaction import TransactionType
from app.core.domain.wallet import WalletType
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from tests.helpers import (
    InMemoryCategoryRepository,
    InMemoryTransactionRepository,
    InMemoryWalletRepository,
)


@pytest.fixture
def wallet_repo() -> InMemoryWalletRepository:
    return InMemoryWalletRepository()


@pytest.fixture
def tx_repo() -> InMemoryTransactionRepository:
    return InMemoryTransactionRepository()


@pytest.fixture
def cat_repo() -> InMemoryCategoryRepository:
    return InMemoryCategoryRepository()


@pytest.fixture
def wallet_svc(wallet_repo, tx_repo) -> WalletService:
    return WalletService(wallet_repo, tx_repo)


@pytest.fixture
def tx_svc(tx_repo, cat_repo, wallet_repo) -> TransactionService:
    rate_svc = Mock(spec=ExchangeRateService)
    rate_svc.get_rate.return_value = Decimal("0.709")
    return TransactionService(tx_repo, cat_repo, rate_svc, wallet_repo)


class TestCreateWallet:
    def test_creates_with_type_and_initial_balance(self, wallet_svc: WalletService) -> None:
        uid = uuid4()
        w = wallet_svc.create(uid, "Family Savings", type=WalletType.SAVINGS,
                              initial_balance=Decimal("500"))
        assert w.type == WalletType.SAVINGS
        assert w.balance == Decimal("500")

    def test_rejects_duplicate_name(self, wallet_svc: WalletService) -> None:
        uid = uuid4()
        wallet_svc.create(uid, "Cash")
        with pytest.raises(ConflictError):
            wallet_svc.create(uid, "cash")

    def test_rejects_blank_name(self, wallet_svc: WalletService) -> None:
        with pytest.raises(ValidationError):
            wallet_svc.create(uuid4(), "   ")


class TestBalance:
    def test_income_adds_expense_subtracts(self, wallet_svc, tx_svc, cat_repo) -> None:
        uid = uuid4()
        cat_repo.save(Category(uid, "Salary", CategoryType.INCOME))
        cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        w = wallet_svc.create(uid, "Cash", initial_balance=Decimal("100"))

        tx_svc.create(uid, Decimal("1000"), "JOD", "Salary", date(2025, 1, 5), wallet_id=w.id)
        tx_svc.create(uid, Decimal("250"), "JOD", "Food", date(2025, 1, 6), wallet_id=w.id)

        refreshed = wallet_svc.get_wallet(w.id, uid)
        assert refreshed.balance == Decimal("850")  # 100 + 1000 - 250

    def test_deleting_transaction_restores_balance(self, wallet_svc, tx_svc, cat_repo) -> None:
        uid = uuid4()
        cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        w = wallet_svc.create(uid, "Cash", initial_balance=Decimal("100"))
        tx = tx_svc.create(uid, Decimal("30"), "JOD", "Food", date(2025, 1, 6), wallet_id=w.id)
        assert wallet_svc.get_wallet(w.id, uid).balance == Decimal("70")
        tx_svc.delete(tx.id, uid)
        assert wallet_svc.get_wallet(w.id, uid).balance == Decimal("100")


class TestUpdateWallet:
    def test_renames_and_archives(self, wallet_svc: WalletService) -> None:
        uid = uuid4()
        w = wallet_svc.create(uid, "Old Name")
        updated = wallet_svc.update(w.id, uid, name="New Name", is_active=False)
        assert updated.name == "New Name"
        assert updated.is_active is False
        assert wallet_svc.list_wallets(uid) == []
        assert len(wallet_svc.list_wallets(uid, include_inactive=True)) == 1

    def test_raises_for_unknown(self, wallet_svc: WalletService) -> None:
        with pytest.raises(NotFoundError):
            wallet_svc.update(uuid4(), uuid4(), name="X")


class TestDeleteWallet:
    def test_deletes_empty_wallet(self, wallet_svc: WalletService) -> None:
        uid = uuid4()
        w = wallet_svc.create(uid, "Temp")
        assert wallet_svc.delete(w.id, uid) is True

    def test_refuses_wallet_with_transactions(self, wallet_svc, tx_svc, cat_repo) -> None:
        uid = uuid4()
        cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        w = wallet_svc.create(uid, "Cash")
        tx_svc.create(uid, Decimal("10"), "JOD", "Food", date(2025, 1, 6), wallet_id=w.id)
        with pytest.raises(ConflictError):
            wallet_svc.delete(w.id, uid)


class TestTransfer:
    def test_moves_money_between_wallets(self, wallet_svc, tx_svc) -> None:
        uid = uuid4()
        src = wallet_svc.create(uid, "Family Savings", type=WalletType.SAVINGS,
                                initial_balance=Decimal("1000"))
        dst = wallet_svc.create(uid, "Held Money", type=WalletType.CASH)

        out_leg, in_leg = tx_svc.transfer(
            uid, src.id, dst.id, Decimal("300"), "JOD", date(2025, 1, 10),
        )
        assert out_leg.type == TransactionType.TRANSFER_OUT
        assert in_leg.type == TransactionType.TRANSFER_IN
        assert out_leg.transfer_id == in_leg.transfer_id

        assert wallet_svc.get_wallet(src.id, uid).balance == Decimal("700")
        assert wallet_svc.get_wallet(dst.id, uid).balance == Decimal("300")

    def test_rejects_same_wallet(self, wallet_svc, tx_svc) -> None:
        uid = uuid4()
        w = wallet_svc.create(uid, "Cash")
        with pytest.raises(ValidationError):
            tx_svc.transfer(uid, w.id, w.id, Decimal("10"), "JOD", date(2025, 1, 10))

    def test_rejects_foreign_wallet(self, wallet_svc, tx_svc) -> None:
        uid, other = uuid4(), uuid4()
        mine = wallet_svc.create(uid, "Mine")
        theirs = wallet_svc.create(other, "Theirs")
        with pytest.raises(ValidationError):
            tx_svc.transfer(uid, mine.id, theirs.id, Decimal("10"), "JOD", date(2025, 1, 10))

    def test_deleting_one_leg_deletes_both(self, wallet_svc, tx_svc) -> None:
        uid = uuid4()
        src = wallet_svc.create(uid, "A", initial_balance=Decimal("100"))
        dst = wallet_svc.create(uid, "B")
        out_leg, _ = tx_svc.transfer(uid, src.id, dst.id, Decimal("40"), "JOD", date(2025, 1, 10))

        tx_svc.delete(out_leg.id, uid)
        assert wallet_svc.get_wallet(src.id, uid).balance == Decimal("100")
        assert wallet_svc.get_wallet(dst.id, uid).balance == Decimal("0")

    def test_transfer_excluded_from_spending(self, wallet_svc, tx_svc, tx_repo) -> None:
        uid = uuid4()
        src = wallet_svc.create(uid, "A", initial_balance=Decimal("100"))
        dst = wallet_svc.create(uid, "B")
        tx_svc.transfer(uid, src.id, dst.id, Decimal("40"), "JOD", date(2025, 1, 10))
        spending = tx_repo.monthly_spending_by_category(uid, 2025, 1)
        assert spending == {}
