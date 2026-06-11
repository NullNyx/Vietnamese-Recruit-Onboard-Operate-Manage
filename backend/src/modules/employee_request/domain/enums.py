"""Enums for the Employee Request module."""

from enum import Enum


class RequestType(str, Enum):
    """Type of employee request."""

    OVERTIME = "overtime"


class RequestStatus(str, Enum):
    """Lifecycle status of an employee request."""

    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
