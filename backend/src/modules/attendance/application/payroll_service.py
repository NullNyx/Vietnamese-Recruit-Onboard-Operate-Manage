"""Payroll business logic service.

Handles salary calculation (Gross → Net), payroll record creation,
and tax/insurance deductions according to Vietnamese labor law.
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from src.modules.attendance.domain.entities import PayrollRecord
from src.modules.attendance.infrastructure.attendance_repository import (
    AttendanceRepository,
)
from src.modules.attendance.infrastructure.payroll_repository import (
    PayrollRepository,
)
from src.modules.attendance.infrastructure.settings_repository import (
    SettingsRepository,
)


# Vietnamese labor law constants (2024)
INSURANCE_EMPLOYEE_RATE = Decimal("0.105")  # 10.5% = 8% BHXH + 1.5% BHYT + 1% BHTN
INSURANCE_COMPANY_RATE = Decimal("0.215")  # 21.5% = 17.5% BHXH + 3% BHYT + 1% BHTN

PERSONAL_DEDUCTION = Decimal("11000000")  # 11M VND/month
DEPENDENT_DEDUCTION = Decimal("4400000")  # 4.4M VND/person/month

# Tax brackets (progressive)
TAX_BRACKETS = [
    (Decimal("5000000"), Decimal("0.05"), Decimal("0")),
    (Decimal("10000000"), Decimal("0.10"), Decimal("250000")),
    (Decimal("18000000"), Decimal("0.15"), Decimal("750000")),
    (Decimal("32000000"), Decimal("0.20"), Decimal("1650000")),
    (Decimal("50000000"), Decimal("0.25"), Decimal("3250000")),
    (Decimal("80000000"), Decimal("0.30"), Decimal("5850000")),
    (Decimal("80000000"), Decimal("0.35"), Decimal("9850000")),
]

MIN_INSURANCE_SALARY = Decimal("4420000")  # 2024 minimum
MAX_INSURANCE_SALARY = Decimal("29800000")  # 2024 maximum


class PayrollError(Exception):
    """Base exception for payroll operations."""

    pass


class PayrollService:
    """Service for payroll calculation and management."""

    def __init__(
        self,
        payroll_repository: PayrollRepository,
        attendance_repository: AttendanceRepository,
        settings_repository: SettingsRepository,
    ) -> None:
        self.payroll_repo = payroll_repository
        self.attendance_repo = attendance_repo
        self.settings_repo = settings_repository

    async def calculate_payroll(
        self,
        employee_id: UUID,
        month: int,
        year: int,
    ) -> PayrollRecord:
        """Calculate payroll for an employee for a given month.

        Formula:
        1. Salary based on work days
        2. Add overtime amount
        3. Add allowances
        4. Subtract insurance (employee portion)
        5. Calculate taxable income after deductions
        6. Calculate personal income tax
        7. Net = Total - Insurance - Tax

        Args:
            employee_id: UUID of the employee.
            month: Month (1-12).
            year: Year.

        Returns:
            The calculated PayrollRecord.
        """
        # Get salary config for employee
        salary_config = await self.settings_repo.get_salary_config_by_employee(employee_id)
        if salary_config is None:
            raise PayrollError("Salary config not found for employee")

        # Get attendance for the month
        records, _ = await self.attendance_repo.list_by_employee(
            employee_id, month, year
        )

        # Calculate work days
        work_days_actual = Decimal(str(len([r for r in records if r.checkout_time])))
        
        # Calculate work hours
        total_hours = sum(float(r.work_hours or 0) for r in records)
        
        # 1. Salary based on days
        daily_rate = salary_config.gross_salary / Decimal(str(salary_config.work_days_per_month))
        salary_based_on_days = daily_rate * work_days_actual

        # 2. Overtime (simplified - auto-calculated from attendance)
        # TODO: Add overtime calculation when OT module is ready
        overtime_amount = Decimal("0")

        # 3. Allowances (simplified)
        # TODO: Add allowance calculation when Allowance module is ready
        total_allowances = Decimal("0")

        # Gross + OT + Allowances
        total_income = salary_based_on_days + overtime_amount + total_allowances

        # 4. Insurance (employee portion)
        insurance_base = min(max(salary_config.gross_salary, MIN_INSURANCE_SALARY), MAX_INSURANCE_SALARY)
        insurance_employee = insurance_base * INSURANCE_EMPLOYEE_RATE

        # 5. Taxable income
        taxable_income = (
            salary_based_on_days  # Use daily-based salary for tax
            + overtime_amount
            + total_allowances
            - insurance_employee
            - PERSONAL_DEDUCTION
        )
        taxable_income = max(taxable_income, Decimal("0"))

        # 6. Personal Income Tax (progressive)
        personal_income_tax = self._calculate_progressive_tax(taxable_income)

        # 7. Net salary
        net_salary = total_income - insurance_employee - personal_income_tax

        # Create or update payroll record
        existing = await self.payroll_repo.get_by_employee_month(employee_id, month, year)

        if existing:
            existing.gross_salary = salary_config.gross_salary
            existing.work_days_actual = work_days_actual
            existing.salary_based_on_days = salary_based_on_days
            existing.overtime_amount = overtime_amount
            existing.total_allowances = total_allowances
            existing.insurance_employee = insurance_employee
            existing.insurance_company = insurance_base * INSURANCE_COMPANY_RATE
            existing.taxable_income = taxable_income
            existing.personal_income_tax = personal_income_tax
            existing.net_salary = net_salary
            return await self.payroll_repo.update(existing)
        else:
            record = PayrollRecord(
                employee_id=employee_id,
                month=month,
                year=year,
                gross_salary=salary_config.gross_salary,
                work_days_actual=work_days_actual,
                salary_based_on_days=salary_based_on_days,
                overtime_amount=overtime_amount,
                total_allowances=total_allowances,
                insurance_employee=insurance_employee,
                insurance_company=insurance_base * INSURANCE_COMPANY_RATE,
                taxable_income=taxable_income,
                personal_income_tax=personal_income_tax,
                net_salary=net_salary,
            )
            return await self.payroll_repo.create(record)

    async def get_payslip(
        self,
        employee_id: UUID,
        month: int,
        year: int,
    ) -> PayrollRecord | None:
        """Get payslip for an employee."""
        return await self.payroll_repo.get_by_employee_month(employee_id, month, year)

    async def lock_payroll(
        self,
        employee_id: UUID,
        month: int,
        year: int,
        locked_by: UUID,
    ) -> PayrollRecord:
        """Lock payroll for a specific employee and month."""
        record = await self.payroll_repo.get_by_employee_month(employee_id, month, year)
        if record is None:
            raise PayrollError("Payroll record not found")
        
        return await self.payroll_repo.lock_payroll(record, locked_by)

    def _calculate_progressive_tax(self, taxable_income: Decimal) -> Decimal:
        """Calculate personal income tax using progressive brackets.

        Args:
            taxable_income: Taxable income after deductions.

        Returns:
            Total tax amount.
        """
        if taxable_income <= 0:
            return Decimal("0")

        tax = Decimal("0")
        remaining = taxable_income
        prev_limit = Decimal("0")

        for bracket_max, rate, deduction in TAX_BRACKETS:
            if remaining <= 0:
                break

            bracket_width = bracket_max - prev_limit
            taxable_in_bracket = min(remaining, bracket_width)

            if taxable_in_bracket > 0:
                tax += taxable_in_bracket * rate - deduction

            remaining -= taxable_in_bracket
            prev_limit = bracket_max

        return max(tax, Decimal("0"))
