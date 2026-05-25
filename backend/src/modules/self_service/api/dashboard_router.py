"""ESS Dashboard Router.

Provides the employee self-service dashboard endpoint that returns
aggregated data including today's attendance status, pending request
counts, monthly summary, and annual leave balance.

All endpoints enforce ownership via the `check_ess_rate_limit` dependency,
which authenticates the employee and applies rate limiting.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.modules.self_service.api.rate_limiter import check_ess_rate_limit
from src.modules.self_service.api.schemas import ESSDashboardResponse
from src.modules.self_service.application.ess_dashboard_service import (
    ESSDashboardService,
)
from src.modules.self_service.container import get_ess_dashboard_service

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

EmployeeIdDep = Annotated[UUID, Depends(check_ess_rate_limit)]
DashboardServiceDep = Annotated[ESSDashboardService, Depends(get_ess_dashboard_service)]

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

dashboard_router = APIRouter(prefix="/dashboard", tags=["ess-dashboard"])


@dashboard_router.get("", response_model=ESSDashboardResponse)
async def get_dashboard(
    employee_id: EmployeeIdDep,
    service: DashboardServiceDep,
) -> ESSDashboardResponse:
    """Get aggregated dashboard data for the authenticated employee.

    Returns a unified overview including:
    - Today's attendance status (not_checked_in, checked_in, checked_out)
    - Count of pending leave requests
    - Count of pending overtime requests
    - Current month's attendance summary (days worked, absent, total hours)
    - Remaining annual leave balance

    Requirements: 11.1, 11.5
    """
    return await service.get_dashboard(employee_id)
