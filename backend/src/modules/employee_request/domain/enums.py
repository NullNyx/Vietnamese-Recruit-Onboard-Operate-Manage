"""Enums for the Employee Request module."""

from enum import Enum


class RequestType(str, Enum):
    """Type of employee request."""

    OVERTIME = "overtime"
    LEAVE = "leave"


class LeaveType(str, Enum):
    """Type of leave request."""

    ANNUAL = "annual"
    SICK = "sick"
    UNPAID = "unpaid"
    OTHER = "other"


class RequestStatus(str, Enum):
    """Lifecycle status of an employee request."""

    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
