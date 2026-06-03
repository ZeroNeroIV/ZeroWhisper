"""Analytics API routes — cash flow, Sankey, heatmap, net worth."""
from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.application.analytics_service import AnalyticsService
from app.core.domain.user import User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _get_service(request: Request, session: Session = Depends(get_session)) -> AnalyticsService:
    return request.app.state.container.analytics_service(session)


@router.get("/cash-flow")
def cash_flow(
    request: Request,
    user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(_get_service),
    from_date: str | None = None,
    to_date: str | None = None,
):
    df = date.fromisoformat(from_date) if from_date else date.today().replace(day=1)
    dt = date.fromisoformat(to_date) if to_date else date.today()
    return service.get_cash_flow(user.id, df, dt)


@router.get("/sankey")
def sankey(
    request: Request,
    user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(_get_service),
    year: int | None = None,
    month: int | None = None,
):
    today = date.today()
    y = year or today.year
    m = month or today.month
    return service.get_sankey(user.id, y, m)


@router.get("/heatmap")
def heatmap(
    request: Request,
    user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(_get_service),
    year: int | None = None,
    month: int | None = None,
):
    today = date.today()
    y = year or today.year
    m = month or today.month
    return service.get_heatmap(user.id, y, m)


@router.get("/net-worth")
def net_worth(
    request: Request,
    user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(_get_service),
):
    return service.get_net_worth_trend(user.id)
