"""Domain layer for the Employee Management module."""

from src.modules.employee.domain.contract import Contract
from src.modules.employee.domain.contract_amendment import ContractAmendment
from src.modules.employee.domain.contract_template import ContractTemplate
from src.modules.employee.domain.employment_event import EmploymentEvent
from src.modules.employee.domain.entities import (
    Department,
    Employee,
    EmployeeDocument,
    Position,
)

__all__ = [
    "Contract",
    "ContractAmendment",
    "ContractTemplate",
    "Department",
    "Employee",
    "EmployeeDocument",
    "EmploymentEvent",
    "Position",
]
