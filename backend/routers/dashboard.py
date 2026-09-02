"""
routers/dashboard.py
"""

from fastapi import APIRouter
from schemas import DashboardSummary
from data_loader import get_data
from services.dashboard_service import get_summary

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Dashboard KPI summary",
    description="Returns counts and priority breakdowns for the main dashboard cards.",
)
def dashboard_summary():
    d = get_data()
    return get_summary(d)
