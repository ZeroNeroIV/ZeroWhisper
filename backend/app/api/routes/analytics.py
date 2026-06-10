from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends

from app.api.deps import ContainerDep, SessionDep, UserDep
from app.application.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/cash-flow")
def cash_flow(
    container: ContainerDep,
    session: SessionDep,
    user: UserDep,
    from_date: str | None = None,
    to_date: str | None = None,
):
    df = date.fromisoformat(from_date) if from_date else date.today().replace(day=1)
    dt = date.fromisoformat(to_date) if to_date else date.today()
    service: AnalyticsService = container.analytics_service(session)
    return service.get_cash_flow(user.id, df, dt)


@router.get("/sankey")
def sankey(
    container: ContainerDep,
    session: SessionDep,
    user: UserDep,
    year: int | None = None,
    month: int | None = None,
):
    today = date.today()
    y = year or today.year
    m = month or today.month
    service: AnalyticsService = container.analytics_service(session)
    return service.get_sankey(user.id, y, m)


@router.get("/heatmap")
def heatmap(
    container: ContainerDep,
    session: SessionDep,
    user: UserDep,
    year: int | None = None,
    month: int | None = None,
):
    today = date.today()
    y = year or today.year
    m = month or today.month
    service: AnalyticsService = container.analytics_service(session)
    return service.get_heatmap(user.id, y, m)


@router.get("/net-worth")
def net_worth(
    container: ContainerDep,
    session: SessionDep,
    user: UserDep,
):
    service: AnalyticsService = container.analytics_service(session)
    return service.get_net_worth_trend(user.id)
