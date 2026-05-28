"""Domain enums for the Gmail Integration module.

Defines enumeration types used throughout the Gmail module to represent
connection states and email classification categories.
"""

from enum import StrEnum


class ConnectionStatus(StrEnum):
    """Represents the current state of the Gmail OAuth2 connection.

    - connected: OAuth_Grant exists, is_valid=true, token not expired.
    - disconnected: No OAuth_Grant exists with Gmail scopes.
    - token_expired: OAuth_Grant exists but is_valid=false.
    """

    connected = "connected"
    disconnected = "disconnected"
    token_expired = "token_expired"


class EmailCategory(StrEnum):
    """Classification category for emails processed by VroomHR.

    Used to assign Gmail labels (VroomHR/{category}) and track
    email processing pipeline stage. Designed for Vietnamese HR context.
    """

    # Recruitment pipeline
    recruitment = "recruitment"
    interview = "interview"
    offer = "offer"
    onboarding = "onboarding"

    # Employee relations
    leave_request = "leave_request"
    payroll = "payroll"
    employee_request = "employee_request"
    resignation = "resignation"
    complaint = "complaint"

    # External
    vendor = "vendor"
    insurance = "insurance"

    # Internal & compliance
    internal = "internal"
    compliance = "compliance"

    # System
    notification = "notification"
    uncategorized = "uncategorized"
