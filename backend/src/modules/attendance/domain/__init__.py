"""Domain entities for the Attendance & Payroll module."""

from src.modules.attendance.domain.entities import (
    Allowance,
    AttendanceRecord,
    AttendanceSettings,
    OvertimeConfig,
    PayrollRecord,
    SalaryConfig,
    WorkShift,
)

__all__ = [
    "AttendanceRecord",
    "WorkShift",
    "AttendanceSettings",
    "OvertimeConfig",
    "SalaryConfig",
    "Allowance",
    "PayrollRecord",
]
