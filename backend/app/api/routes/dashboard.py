from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ContainerDep, SessionDep, UserDep
from app.application.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(
    container: ContainerDep,
    session: SessionDep,
    user: UserDep,
):
    service: AnalyticsService = container.analytics_service(session)
    return service.get_dashboard_summary(user.id)
