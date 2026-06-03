"""Dashboard API routes — summary endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.application.analytics_service import AnalyticsService
from app.core.domain.user import User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _get_service(request: Request, session: Session = Depends(get_session)) -> AnalyticsService:
    return request.app.state.container.analytics_service(session)


@router.get("/summary")
def summary(
    request: Request,
    user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(_get_service),
):
    return service.get_dashboard_summary(user.id)
