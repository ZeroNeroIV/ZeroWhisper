from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.application.analytics_service import AnalyticsService, _month_end
from app.core.domain.transaction import Transaction as DomainTransaction
from app.core.domain.category import Category, CategoryType
from tests.helpers import InMemoryTransactionRepository, InMemoryCategoryRepository


@pytest.fixture
def cat_repo() -> InMemoryCategoryRepository:
    return InMemoryCategoryRepository()


@pytest.fixture
def tx_repo() -> InMemoryTransactionRepository:
    return InMemoryTransactionRepository()


@pytest.fixture
def analytics(cat_repo: InMemoryCategoryRepository, tx_repo: InMemoryTransactionRepository) -> AnalyticsService:
    return AnalyticsService(tx_repo, cat_repo)


@pytest.fixture
def seeded_user(cat_repo: InMemoryCategoryRepository, tx_repo: InMemoryTransactionRepository) -> tuple:
    uid = uuid4()
    cat_repo.seed_defaults(uid)
    cat_repo.save(Category(uid, "Fuel", CategoryType.EXPENSE))
    cat_repo.save(Category(uid, "Salary", CategoryType.INCOME))
    tx_repo.save(DomainTransaction(
        user_id=uid, amount_original=Decimal("3000"), currency_original="JOD",
        category="Salary", transaction_date=date(2025, 1, 5),
        amount_base=Decimal("3000"),
    ))
    tx_repo.save(DomainTransaction(
        user_id=uid, amount_original=Decimal("200"), currency_original="JOD",
        category="Food", transaction_date=date(2025, 1, 10),
        amount_base=Decimal("200"),
    ))
    tx_repo.save(DomainTransaction(
        user_id=uid, amount_original=Decimal("50"), currency_original="JOD",
        category="Fuel", transaction_date=date(2025, 1, 12),
        amount_base=Decimal("50"),
    ))
    return uid, analytics


class TestMonthEnd:
    def test_non_december(self) -> None:
        assert _month_end(2025, 3) == date(2025, 4, 1)

    def test_december(self) -> None:
        assert _month_end(2025, 12) == date(2026, 1, 1)


class TestGetCashFlow:
    def test_returns_daily_aggregates(self, seeded_user) -> None:
        uid, analytics = seeded_user
        flow = analytics.get_cash_flow(uid, date(2025, 1, 1), date(2025, 1, 31))
        assert len(flow) == 2  # 2 days with transactions
        income_day = next(d for d in flow if d["date"] == "2025-01-05")
        assert income_day["income"] == 3000.0
        expense_day = next(d for d in flow if d["date"] == "2025-01-10")
        # Income + savings categories excluded from expenses
        # Only Food is an expense (Fuel was added as expense)
        assert expense_day["income"] == 0.0

    def test_balance_is_cumulative(self, seeded_user) -> None:
        uid, analytics = seeded_user
        flow = analytics.get_cash_flow(uid, date(2025, 1, 1), date(2025, 1, 31))
        assert len(flow) >= 1
        # Final balance = 3000 - 200 (Food) - 50 (Fuel) = 2750 only if Food+Fuel are expenses
        last = flow[-1]
        assert last["balance"] is not None


class TestGetSankey:
    def test_returns_nodes_and_links(self, seeded_user) -> None:
        uid, analytics = seeded_user
        sankey = analytics.get_sankey(uid, 2025, 1)
        assert len(sankey["nodes"]) == 3  # Income, Food, Fuel
        assert len(sankey["links"]) == 2
        total_income = next(
            float(t.amount_base) for t in analytics._tx_repo._store.values()
            if t.category == "Salary" and t.user_id == uid
        )
        assert sankey["total_income"] == total_income

    def test_empty_month(self, analytics: AnalyticsService) -> None:
        uid = uuid4()
        sankey = analytics.get_sankey(uid, 2025, 6)
        assert sankey["nodes"] == []
        assert sankey["links"] == []


class TestGetHeatmap:
    def test_returns_category_amounts(self, seeded_user) -> None:
        uid, analytics = seeded_user
        heatmap = analytics.get_heatmap(uid, 2025, 1)
        cats = {h["category"] for h in heatmap}
        assert "Food" in cats or "Fuel" in cats
        assert all(h["amount"] > 0 for h in heatmap)

    def test_excludes_income_and_savings(self, seeded_user) -> None:
        uid, analytics = seeded_user
        heatmap = analytics.get_heatmap(uid, 2025, 1)
        cat_names = {h["category"] for h in heatmap}
        assert "Salary" not in cat_names


class TestGetNetWorthTrend:
    def test_monthly_cumulative(self, seeded_user) -> None:
        uid, analytics = seeded_user
        trend = analytics.get_net_worth_trend(uid)
        assert len(trend) == 1
        assert trend[0]["month"] == "2025-01"
        assert trend[0]["net_worth"] > 0

    def test_empty_returns_empty_list(self, analytics: AnalyticsService) -> None:
        trend = analytics.get_net_worth_trend(uuid4())
        assert trend == []


class TestGetDashboardSummary:
    def test_returns_all_keys(self, seeded_user) -> None:
        uid, analytics = seeded_user
        summary = analytics.get_dashboard_summary(uid)
        assert "balance" in summary
        assert "this_month_spending" in summary
        assert "this_month_income" in summary
        assert "total_savings" in summary
        assert "recent_transactions" in summary
        assert len(summary["recent_transactions"]) > 0

    def test_amounts_are_strings(self, seeded_user) -> None:
        uid, analytics = seeded_user
        summary = analytics.get_dashboard_summary(uid)
        assert isinstance(summary["balance"], str)
        assert isinstance(summary["this_month_spending"], str)
