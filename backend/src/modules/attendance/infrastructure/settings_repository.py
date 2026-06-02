"""Repository for AttendanceSettings entity."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.attendance.domain.entities import (
    Allowance,
    AttendanceSettings,
    OvertimeConfig,
    SalaryConfig,
    WorkShift,
)


class SettingsRepository:
    """Handles AttendanceSettings and related config entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_attendance_settings(self) -> AttendanceSettings | None:
        """Get the company-wide attendance settings (singleton)."""
        statement = select(AttendanceSettings).limit(1)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def create_or_update_attendance_settings(
        self, settings: AttendanceSettings
    ) -> AttendanceSettings:
        """Create or update the singleton attendance settings."""
        existing = await self.get_attendance_settings()
        if existing:
            # Update existing
            for key, value in settings.__dict__.items():
                if key != "id" and value is not None:
                    setattr(existing, key, value)
            existing.updated_at = datetime.now(UTC)
            self.session.add(existing)
            await self.session.flush()
            return existing
        else:
            # Create new
            self.session.add(settings)
            await self.session.flush()
            return settings

    async def list_shifts(self, is_active: bool | None = None) -> list[WorkShift]:
        """List all work shifts."""
        statement = select(WorkShift)
        if is_active is not None:
            statement = statement.where(WorkShift.is_active == is_active)
        statement = statement.order_by(WorkShift.start_time)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_shift_by_id(self, shift_id) -> WorkShift | None:
        """Get shift by ID."""
        statement = select(WorkShift).where(WorkShift.id == shift_id)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def create_shift(self, shift: WorkShift) -> WorkShift:
        """Create a new work shift."""
        self.session.add(shift)
        await self.session.flush()
        return shift

    async def update_shift(self, shift: WorkShift) -> WorkShift:
        """Update an existing work shift."""
        self.session.add(shift)
        await self.session.flush()
        return shift

    async def get_overtime_configs(self) -> list[OvertimeConfig]:
        """Get all overtime configurations."""
        statement = select(OvertimeConfig).where(OvertimeConfig.is_active == True)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_salary_config_by_employee(self, employee_id) -> SalaryConfig | None:
        """Get salary config for an employee."""
        statement = select(SalaryConfig).where(SalaryConfig.employee_id == employee_id)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def create_salary_config(self, config: SalaryConfig) -> SalaryConfig:
        """Create salary config for an employee."""
        self.session.add(config)
        await self.session.flush()
        return config

    async def update_salary_config(self, config: SalaryConfig) -> SalaryConfig:
        """Update salary config."""
        self.session.add(config)
        await self.session.flush()
        return config

    async def list_allowances(self, is_active: bool | None = None) -> list[Allowance]:
        """List all allowances."""
        statement = select(Allowance)
        if is_active is not None:
            statement = statement.where(Allowance.is_active == is_active)
        result = await self.session.execute(statement)
        return list(result.scalars().all())
