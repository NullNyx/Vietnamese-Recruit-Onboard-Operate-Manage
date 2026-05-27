"""Main ESS router aggregating all sub-routers.

Combines profile, attendance, leave, overtime, document, schedule,
and dashboard sub-routers under the /api/v1/ess prefix.

Rate limiting is enforced per-endpoint via the `check_ess_rate_limit`
dependency in each sub-router, so no additional rate limiting is
applied at this aggregation level.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.modules.self_service.api.attendance_router import attendance_router
from src.modules.self_service.api.document_router import document_router
from src.modules.self_service.api.leave_router import leave_router
from src.modules.self_service.api.overtime_router import overtime_router
from src.modules.self_service.api.profile_router import profile_router
from src.modules.self_service.api.schedule_router import schedule_router

ess_router = APIRouter(prefix="/api/v1/ess", tags=["employee-self-service"])

# Include all sub-routers. Each sub-router defines its own prefix
# (e.g., /profile, /attendance, /leave, /overtime, /documents, /schedule).
# Rate limiting is applied per-endpoint via check_ess_rate_limit dependency.
ess_router.include_router(profile_router)
ess_router.include_router(attendance_router)
ess_router.include_router(leave_router)
ess_router.include_router(overtime_router)
ess_router.include_router(document_router)
ess_router.include_router(schedule_router)

from src.modules.self_service.api.dashboard_router import dashboard_router

ess_router.include_router(dashboard_router)
