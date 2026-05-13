from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
import datetime as dt

from app.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.services import analytics_service

router = APIRouter()


@router.get("/cash-flow")
def cash_flow(
    from_date: dt.date = Query(default_factory=lambda: dt.date.today().replace(day=1)),
    to_date: dt.date = Query(default_factory=dt.date.today),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return analytics_service.get_cash_flow(session, current_user.id, from_date, to_date)


@router.get("/sankey")
def sankey(
    year: int = Query(default_factory=lambda: dt.date.today().year),
    month: int = Query(default_factory=lambda: dt.date.today().month),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return analytics_service.get_sankey(session, current_user.id, year, month)


@router.get("/heatmap")
def heatmap(
    year: int = Query(default_factory=lambda: dt.date.today().year),
    month: int = Query(default_factory=lambda: dt.date.today().month),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return analytics_service.get_heatmap(session, current_user.id, year, month)


@router.get("/net-worth")
def net_worth(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return analytics_service.get_net_worth_trend(session, current_user.id)
