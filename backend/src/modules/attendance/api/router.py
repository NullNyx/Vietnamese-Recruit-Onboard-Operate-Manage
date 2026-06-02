"""FastAPI router for Attendance & Payroll module.

Exposes endpoints for check-in/check-out, attendance history,
settings management, and payroll calculation.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.modules.attendance.container import (
    get_attendance_service,
    get_payroll_service,
    get_settings_repository,
)

# Type aliases for dependency injection
from src.modules.attendance.application.attendance_service import AttendanceService
from src.modules.attendance.application.payroll_service import PayrollService
from src.modules.attendance.infrastructure.settings_repository import SettingsRepository

AttendanceServiceDep = Annotated[
    AttendanceService, Depends(get_attendance_service)
]
PayrollServiceDep = Annotated[PayrollService, Depends(get_payroll_service)]
SettingsRepoDep = Annotated[SettingsRepository, Depends(get_settings_repository)]

from src.modules.attendance.api.schemas import (
    AttendanceErrorResponse,
    AttendanceHistoryResponse,
    AttendanceRecordResponse,
    AttendanceSettingsResponse,
    AttendanceSettingsUpdate,
    CheckinRequest,
    CheckinResponse,
    CheckoutRequest,
    CheckoutResponse,
    HREditRecordRequest,
    PayrollCalculateRequest,
    PayrollRecordResponse,
    SalaryConfigRequest,
    SalaryConfigResponse,
)
from src.modules.attendance.application.attendance_service import (
    AttendanceService,
    AttendanceError,
    CheckinError,
    CheckoutError,
)
from src.modules.attendance.application.payroll_service import (
    PayrollError,
    PayrollService,
)
from src.modules.attendance.container import (
    get_attendance_service,
    get_payroll_service,
    get_settings_repository,
)

router = APIRouter(prefix="/api/v1/attendance", tags=["attendance"])
payroll_router = APIRouter(prefix="/api/v1/payroll", tags=["payroll"])


# ===================== Check-in/Check-out =====================


@router.post(
    "/checkin",
    response_model=CheckinResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": AttendanceErrorResponse},
    },
)
async def checkin(
    request: CheckinRequest,
    service: AttendanceServiceDep,
) -> CheckinResponse:
    """Perform a check-in for an employee."""
    try:
        timestamp = request.timestamp or datetime.now(UTC)
        record = await service.checkin(
            employee_id=request.employee_id,
            timestamp=timestamp,
            ip_address=request.ip_address,
            source=request.source,
            location_id=request.location_id,
        )
        return CheckinResponse(
            id=record.id,
            employee_id=record.employee_id,
            checkin_time=record.checkin_time,
            source=record.source,
            is_late=record.is_late,
            late_minutes=record.late_minutes,
        )
    except CheckinError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": AttendanceErrorResponse},
    },
)
async def checkout(
    request: CheckoutRequest,
    service: AttendanceServiceDep,
) -> CheckoutResponse:
    """Perform a check-out for an employee."""
    try:
        timestamp = request.timestamp or datetime.now(UTC)
        record = await service.checkout(
            employee_id=request.employee_id,
            timestamp=timestamp,
        )
        return CheckoutResponse(
            id=record.id,
            employee_id=record.employee_id,
            checkin_time=record.checkin_time,
            checkout_time=record.checkout_time,
            work_hours=record.work_hours,
            is_early_leave=record.is_early_leave,
            early_minutes=record.early_minutes,
        )
    except CheckoutError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===================== Attendance Records =====================


@router.get(
    "/history",
    response_model=AttendanceHistoryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_attendance_history(
    employee_id: UUID,
    service: AttendanceServiceDep,
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2020),
    page: int = Query(1, ge=1),
    page_size: int = Query(31, ge=1, le=100),
) -> AttendanceHistoryResponse:
    """Get attendance history for an employee (employee view)."""
    records, total = await service.get_attendance_history(
        employee_id, month, year, page, page_size
    )
    items = [
        AttendanceRecordResponse(
            id=r.id,
            employee_id=r.employee_id,
            checkin_time=r.checkin_time,
            checkout_time=r.checkout_time,
            source=r.source,
            work_hours=r.work_hours,
            late_minutes=r.late_minutes,
            early_minutes=r.early_minutes,
            is_late=r.is_late,
            is_early_leave=r.is_early_leave,
            notes=r.notes,
            created_at=r.created_at,
        )
        for r in records
    ]
    return AttendanceHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.put(
    "/records/{record_id}",
    response_model=AttendanceRecordResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": AttendanceErrorResponse},
    },
)
async def hr_edit_record(
    record_id: UUID,
    request: HREditRecordRequest,
    service: AttendanceServiceDep,
    edited_by: UUID | None = Query(None),
) -> AttendanceRecordResponse:
    """HR manually edit an attendance record."""
    try:
        record = await service.hr_edit_record(
            record_id=record_id,
            checkin_time=request.checkin_time,
            checkout_time=request.checkout_time,
            edited_by=edited_by,
            notes=request.notes,
        )
        return AttendanceRecordResponse(
            id=record.id,
            employee_id=record.employee_id,
            checkin_time=record.checkin_time,
            checkout_time=record.checkout_time,
            source=record.source,
            work_hours=record.work_hours,
            late_minutes=record.late_minutes,
            early_minutes=record.early_minutes,
            is_late=record.is_late,
            is_early_leave=record.is_early_leave,
            notes=record.notes,
            created_at=record.created_at,
        )
    except AttendanceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===================== Settings =====================


@router.get(
    "/settings",
    response_model=AttendanceSettingsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_attendance_settings(
    repo: SettingsRepoDep,
) -> AttendanceSettingsResponse:
    """Get company attendance settings."""
    from datetime import time

    settings = await repo.get_attendance_settings()
    if settings is None:
        # Return default settings if none exist
        return AttendanceSettingsResponse(
            id=UUID("00000000-0000-0000-0000-000000000000"),
            work_model="fixed",
            checkin_web_enabled=True,
            checkin_qr_enabled=True,
            checkin_device_enabled=False,
            fixed_start_time=time(8, 0),
            fixed_end_time=time(17, 0),
            fixed_break_start=time(12, 0),
            fixed_break_end=time(13, 0),
            late_tolerance_minutes=10,
            early_leave_tolerance_minutes=10,
            weekly_off_days="saturday",
            ip_whitelist_enabled=False,
            ip_whitelist=None,
        )
    return AttendanceSettingsResponse.model_validate(settings)


@router.put(
    "/settings",
    response_model=AttendanceSettingsResponse,
    status_code=status.HTTP_200_OK,
)
async def update_attendance_settings(
    request: AttendanceSettingsUpdate,
    repo: SettingsRepoDep,
) -> AttendanceSettingsResponse:
    """Update company attendance settings."""
    from src.modules.attendance.domain.entities import AttendanceSettings

    settings = await repo.get_attendance_settings()
    if settings is None:
        # Create new settings
        new_settings = AttendanceSettings(
            work_model=request.work_model or "fixed",
            checkin_web_enabled=request.checkin_web_enabled if request.checkin_web_enabled is not None else True,
            checkin_qr_enabled=request.checkin_qr_enabled if request.checkin_qr_enabled is not None else True,
            checkin_device_enabled=request.checkin_device_enabled if request.checkin_device_enabled is not None else False,
            fixed_start_time=request.fixed_start_time or datetime.strptime("08:00", "%H:%M").time(),
            fixed_end_time=request.fixed_end_time or datetime.strptime("17:00", "%H:%M").time(),
            fixed_break_start=request.fixed_break_start or datetime.strptime("12:00", "%H:%M").time(),
            fixed_break_end=request.fixed_break_end or datetime.strptime("13:00", "%H:%M").time(),
            late_tolerance_minutes=request.late_tolerance_minutes if request.late_tolerance_minutes is not None else 10,
            early_leave_tolerance_minutes=request.early_leave_tolerance_minutes if request.early_leave_tolerance_minutes is not None else 10,
            weekly_off_days=request.weekly_off_days or "saturday",
            ip_whitelist_enabled=request.ip_whitelist_enabled if request.ip_whitelist_enabled is not None else False,
            ip_whitelist=request.ip_whitelist,
        )
        settings = await repo.create_or_update_attendance_settings(new_settings)
    else:
        # Update existing
        if request.work_model is not None:
            settings.work_model = request.work_model
        if request.checkin_web_enabled is not None:
            settings.checkin_web_enabled = request.checkin_web_enabled
        if request.checkin_qr_enabled is not None:
            settings.checkin_qr_enabled = request.checkin_qr_enabled
        if request.checkin_device_enabled is not None:
            settings.checkin_device_enabled = request.checkin_device_enabled
        if request.fixed_start_time is not None:
            settings.fixed_start_time = request.fixed_start_time
        if request.fixed_end_time is not None:
            settings.fixed_end_time = request.fixed_end_time
        if request.fixed_break_start is not None:
            settings.fixed_break_start = request.fixed_break_start
        if request.fixed_break_end is not None:
            settings.fixed_break_end = request.fixed_break_end
        if request.late_tolerance_minutes is not None:
            settings.late_tolerance_minutes = request.late_tolerance_minutes
        if request.early_leave_tolerance_minutes is not None:
            settings.early_leave_tolerance_minutes = request.early_leave_tolerance_minutes
        if request.weekly_off_days is not None:
            settings.weekly_off_days = request.weekly_off_days
        if request.ip_whitelist_enabled is not None:
            settings.ip_whitelist_enabled = request.ip_whitelist_enabled
        if request.ip_whitelist is not None:
            settings.ip_whitelist = request.ip_whitelist
        settings = await repo.create_or_update_attendance_settings(settings)

    return AttendanceSettingsResponse.model_validate(settings)


# ===================== Salary Config =====================


@router.post(
    "/salary",
    response_model=SalaryConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_or_update_salary_config(
    request: SalaryConfigRequest,
    repo: SettingsRepoDep,
) -> SalaryConfigResponse:
    """Create or update salary config for an employee."""
    from src.modules.attendance.domain.entities import SalaryConfig

    existing = await repo.get_salary_config_by_employee(request.employee_id)
    if existing:
        existing.gross_salary = request.gross_salary
        existing.pay_cycle = request.pay_cycle
        existing.work_days_per_month = request.work_days_per_month
        existing.work_hours_per_day = request.work_hours_per_day
        config = await repo.update_salary_config(existing)
    else:
        config = SalaryConfig(
            employee_id=request.employee_id,
            gross_salary=request.gross_salary,
            pay_cycle=request.pay_cycle,
            work_days_per_month=request.work_days_per_month,
            work_hours_per_day=request.work_hours_per_day,
        )
        config = await repo.create_salary_config(config)

    return SalaryConfigResponse.model_validate(config)


@router.get(
    "/salary/{employee_id}",
    response_model=SalaryConfigResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": AttendanceErrorResponse},
    },
)
async def get_salary_config(
    employee_id: UUID,
    repo: SettingsRepoDep,
) -> SalaryConfigResponse:
    """Get salary config for an employee."""
    config = await repo.get_salary_config_by_employee(employee_id)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary config not found",
        )
    return SalaryConfigResponse.model_validate(config)


# ===================== Payroll =====================


@payroll_router.post(
    "/calculate",
    response_model=PayrollRecordResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": AttendanceErrorResponse},
    },
)
async def calculate_payroll(
    employee_id: UUID,
    request: PayrollCalculateRequest,
    service: PayrollServiceDep,
) -> PayrollRecordResponse:
    """Calculate payroll for an employee for a given month."""
    try:
        record = await service.calculate_payroll(
            employee_id=employee_id,
            month=request.month,
            year=request.year,
        )
        return PayrollRecordResponse.model_validate(record)
    except PayrollError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@payroll_router.get(
    "/payslip/{employee_id}",
    response_model=PayrollRecordResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": AttendanceErrorResponse},
    },
)
async def get_payslip(
    employee_id: UUID,
    service: PayrollServiceDep,
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2020),
) -> PayrollRecordResponse:
    """Get payslip for an employee."""
    record = await service.get_payslip(employee_id, month, year)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll record not found",
        )
    return PayrollRecordResponse.model_validate(record)


@payroll_router.post(
    "/lock",
    response_model=PayrollRecordResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": AttendanceErrorResponse},
    },
)
async def lock_payroll(
    employee_id: UUID,
    locked_by: UUID,
    service: PayrollServiceDep,
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2020),
) -> PayrollRecordResponse:
    """Lock payroll for an employee (prevents further edits)."""
    try:
        record = await service.lock_payroll(employee_id, month, year, locked_by)
        return PayrollRecordResponse.model_validate(record)
    except PayrollError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
