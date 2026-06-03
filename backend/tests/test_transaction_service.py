from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.application.transaction_service import TransactionService
from app.application.exchange_rate_service import ExchangeRateService
from app.core.domain.transaction import Transaction as DomainTransaction
from app.core.domain.category import Category, CategoryType
from app.core.exceptions import NotFoundError, ValidationError
from tests.helpers import InMemoryTransactionRepository, InMemoryCategoryRepository


@pytest.fixture
def cat_repo() -> InMemoryCategoryRepository:
    return InMemoryCategoryRepository()


@pytest.fixture
def tx_repo() -> InMemoryTransactionRepository:
    return InMemoryTransactionRepository()


@pytest.fixture
def rate_svc() -> ExchangeRateService:
    mock = Mock(spec=ExchangeRateService)
    mock.get_rate.return_value = Decimal("0.709")
    return mock


@pytest.fixture
def tx_svc(
    tx_repo: InMemoryTransactionRepository,
    cat_repo: InMemoryCategoryRepository,
    rate_svc: ExchangeRateService,
) -> TransactionService:
    cat_repo.seed_defaults(uuid4())
    # clear defaults so we create what we need
    return TransactionService(tx_repo, cat_repo, rate_svc)


class TestCreate:
    def test_creates_jod_transaction(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        tx = tx_svc.create(uid, Decimal("50"), "JOD", "Food", date(2025, 1, 15))
        assert tx.amount_original == Decimal("50")
        assert tx.currency_original == "JOD"
        assert tx.amount_base == Decimal("50")
        assert tx.exchange_rate == Decimal("1.0")
        assert tx.source == "manual"

    def test_creates_usd_transaction(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Rent", CategoryType.EXPENSE))
        tx = tx_svc.create(uid, Decimal("100"), "USD", "Rent", date(2025, 1, 15))
        assert tx.currency_original == "USD"
        assert tx.amount_base == Decimal("70.9")  # 100 * 0.709

    def test_creates_with_override_rate(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Travel", CategoryType.EXPENSE))
        tx = tx_svc.create(
            uid, Decimal("200"), "USD", "Travel", date(2025, 1, 15),
            exchange_rate_override=Decimal("0.800"),
        )
        assert tx.amount_base == Decimal("160.0")

    def test_rejects_invalid_category(self, tx_svc: TransactionService) -> None:
        with pytest.raises(ValidationError, match="Invalid category"):
            tx_svc.create(uuid4(), Decimal("10"), "JOD", "NonExistent", date(2025, 1, 1))

    def test_sets_source(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        tx = tx_svc.create(
            uid, Decimal("10"), "JOD", "Food", date(2025, 1, 1), source="whisper",
        )
        assert tx.source == "whisper"

    def test_rejects_negative_amount(self, tx_svc: TransactionService) -> None:
        with pytest.raises(ValidationError):
            tx_svc.create(uuid4(), Decimal("-5"), "JOD", "Food", date(2025, 1, 1))


class TestGet:
    def test_gets_by_id(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        created = tx_svc.create(uid, Decimal("25"), "JOD", "Food", date(2025, 1, 1))
        fetched = tx_svc.get(created.id, uid)
        assert fetched.id == created.id
        assert fetched.amount_original == Decimal("25")

    def test_raises_not_found(self, tx_svc: TransactionService) -> None:
        with pytest.raises(NotFoundError):
            tx_svc.get(uuid4(), uuid4())

    def test_wont_return_soft_deleted(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        tx = tx_svc.create(uid, Decimal("5"), "JOD", "Food", date(2025, 1, 1))
        tx_svc.delete(tx.id, uid)
        with pytest.raises(NotFoundError):
            tx_svc.get(tx.id, uid)


class TestList:
    def test_lists_user_transactions(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        tx_svc.create(uid, Decimal("10"), "JOD", "Food", date(2025, 1, 1))
        tx_svc.create(uid, Decimal("20"), "JOD", "Food", date(2025, 1, 2))
        items, total = tx_svc.list(uid)
        assert total == 2
        assert len(items) == 2

    def test_filters_by_category(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        tx_svc._cat_repo.save(Category(uid, "Rent", CategoryType.EXPENSE))
        tx_svc.create(uid, Decimal("10"), "JOD", "Food", date(2025, 1, 1))
        tx_svc.create(uid, Decimal("500"), "JOD", "Rent", date(2025, 1, 1))
        items, total = tx_svc.list(uid, category="Food")
        assert total == 1
        assert items[0].category == "Food"

    def test_filters_by_currency(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        tx_svc.create(uid, Decimal("10"), "JOD", "Food", date(2025, 1, 1))
        tx_svc.create(uid, Decimal("20"), "USD", "Food", date(2025, 1, 1))
        items, total = tx_svc.list(uid, currency="USD")
        assert total == 1

    def test_pagination(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        for i in range(5):
            tx_svc.create(uid, Decimal(str(i + 1)), "JOD", "Food", date(2025, 1, 1))
        page1, total = tx_svc.list(uid, page=1, page_size=2)
        assert len(page1) == 2
        assert total == 5
        page2, _ = tx_svc.list(uid, page=2, page_size=2)
        assert len(page2) == 2

    def test_clamps_page_to_positive(self, tx_svc: TransactionService) -> None:
        items, total = tx_svc.list(uuid4(), page=0, page_size=20)
        assert items == []
        assert total == 0

    def test_clamps_page_size(self, tx_svc: TransactionService) -> None:
        items, total = tx_svc.list(uuid4(), page=1, page_size=200)
        assert items == []
        assert total == 0


class TestUpdate:
    def test_updates_category(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        tx_svc._cat_repo.save(Category(uid, "Rent", CategoryType.EXPENSE))
        tx = tx_svc.create(uid, Decimal("10"), "JOD", "Food", date(2025, 1, 1))
        updated = tx_svc.update(tx.id, uid, category="Rent")
        assert updated.category == "Rent"

    def test_updates_amount_recomputes_base(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        tx = tx_svc.create(uid, Decimal("100"), "USD", "Food", date(2025, 1, 1))
        updated = tx_svc.update(tx.id, uid, amount_original=Decimal("200"))
        assert updated.amount_original == Decimal("200")
        assert updated.amount_base == Decimal("141.8")

    def test_updates_description(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        tx = tx_svc.create(uid, Decimal("10"), "JOD", "Food", date(2025, 1, 1))
        updated = tx_svc.update(tx.id, uid, description="Groceries")
        assert updated.description == "Groceries"

    def test_raises_not_found(self, tx_svc: TransactionService) -> None:
        with pytest.raises(NotFoundError):
            tx_svc.update(uuid4(), uuid4(), description="nope")


class TestDelete:
    def test_soft_delete(self, tx_svc: TransactionService) -> None:
        uid = uuid4()
        tx_svc._cat_repo.save(Category(uid, "Food", CategoryType.EXPENSE))
        tx = tx_svc.create(uid, Decimal("10"), "JOD", "Food", date(2025, 1, 1))
        tx_svc.delete(tx.id, uid)
        assert tx_svc._tx_repo.find_by_id(tx.id, uid) is None

    def test_raises_if_missing(self, tx_svc: TransactionService) -> None:
        with pytest.raises(NotFoundError):
            tx_svc.delete(uuid4(), uuid4())
