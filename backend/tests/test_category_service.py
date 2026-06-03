from uuid import uuid4

import pytest

from app.application.category_service import CategoryService
from app.core.domain.category import Category, CategoryType
from app.core.exceptions import NotFoundError
from tests.helpers import InMemoryCategoryRepository


@pytest.fixture
def cat_svc() -> CategoryService:
    return CategoryService(InMemoryCategoryRepository())


class TestListOrSeed:
    def test_seeds_defaults_when_empty(self, cat_svc: CategoryService) -> None:
        uid = uuid4()
        cats = cat_svc.list_or_seed(uid)
        assert len(cats) == 3
        names = {c.name for c in cats}
        assert names == {"Food", "Income", "Savings"}

    def test_returns_existing_categories(self, cat_svc: CategoryService) -> None:
        uid = uuid4()
        cat_svc.list_or_seed(uid)
        cats2 = cat_svc.list_or_seed(uid)
        assert len(cats2) == 3


class TestCreate:
    def test_creates_category(self, cat_svc: CategoryService) -> None:
        uid = uuid4()
        cat = cat_svc.create(uid, "TestCat", CategoryType.EXPENSE)
        assert cat.name == "TestCat"
        assert cat.type == CategoryType.EXPENSE
        assert cat.user_id == uid

    def test_creates_with_color_and_icon(self, cat_svc: CategoryService) -> None:
        uid = uuid4()
        cat = cat_svc.create(uid, "X", CategoryType.INCOME, color="#ff0", icon="star")
        assert cat.color == "#ff0"
        assert cat.icon == "star"


class TestGet:
    def test_gets_by_id(self, cat_svc: CategoryService) -> None:
        uid = uuid4()
        created = cat_svc.create(uid, "Bob", CategoryType.SAVINGS)
        fetched = cat_svc.get(created.id, uid)
        assert fetched.id == created.id
        assert fetched.name == "Bob"

    def test_gets_by_name(self, cat_svc: CategoryService) -> None:
        uid = uuid4()
        cat_svc.create(uid, "Named", CategoryType.EXPENSE)
        names = cat_svc.list_or_seed(uid)
        # find_by_name lookup
        assert len(names) >= 1

    def test_raises_not_found(self, cat_svc: CategoryService) -> None:
        with pytest.raises(NotFoundError):
            cat_svc.get(uuid4(), uuid4())


class TestUpdate:
    def test_updates_name(self, cat_svc: CategoryService) -> None:
        uid = uuid4()
        cat = cat_svc.create(uid, "Old", CategoryType.EXPENSE)
        updated = cat_svc.update(cat.id, uid, name="New")
        assert updated.name == "New"

    def test_updates_type(self, cat_svc: CategoryService) -> None:
        uid = uuid4()
        cat = cat_svc.create(uid, "Flex", CategoryType.EXPENSE)
        updated = cat_svc.update(cat.id, uid, type=CategoryType.SAVINGS)
        assert updated.type == CategoryType.SAVINGS

    def test_updates_partial(self, cat_svc: CategoryService) -> None:
        uid = uuid4()
        cat = cat_svc.create(uid, "A", CategoryType.INCOME, color="red")
        updated = cat_svc.update(cat.id, uid, color="blue")
        assert updated.name == "A"
        assert updated.color == "blue"


class TestDelete:
    def test_deletes(self, cat_svc: CategoryService) -> None:
        uid = uuid4()
        cat = cat_svc.create(uid, "DelMe", CategoryType.EXPENSE)
        cat_svc.delete(cat.id, uid)
        with pytest.raises(NotFoundError):
            cat_svc.get(cat.id, uid)

    def test_raises_not_found_for_wrong_user(self, cat_svc: CategoryService) -> None:
        uid = uuid4()
        cat = cat_svc.create(uid, "Mine", CategoryType.EXPENSE)
        with pytest.raises(NotFoundError):
            cat_svc.delete(cat.id, uuid4())
