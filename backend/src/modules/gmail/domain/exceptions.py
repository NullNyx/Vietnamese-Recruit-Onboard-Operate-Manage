"""Domain exceptions for the Gmail Integration module.

This module defines the exception hierarchy used throughout the Gmail
module to represent business rule violations, API errors, connection
state issues, and outbound email lifecycle errors.
"""


class GmailError(Exception):
    """Base exception for the Gmail module.

    All domain-specific exceptions inherit from this class, enabling
    a single exception handler to catch any Gmail-related error and
    return a consistent JSON error response.

    Attributes:
        status_code: HTTP status code to return to the client.
        error_code: Machine-readable error identifier.
        message: Human-readable error description.
    """

    status_code: int = 500
    error_code: str = "GMAIL_ERROR"
    message: str = "A Gmail module error occurred"

    def __init__(self, message: str | None = None) -> None:
        """Initialize GmailError.

        Args:
            message: Optional custom message override. If not provided,
                the class-level default message is used.
        """
        if message is not None:
            self.message = message
        super().__init__(self.message)


class UnauthorizedException(GmailError):
    """Missing or invalid authentication session.

    Raised when a request lacks valid authentication credentials
    or the session has expired.
    """

    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "Missing or invalid authentication session"


class GmailNotConnectedException(GmailError):
    """Gmail is not connected when an operation requires it.

    Raised when an API operation (fetch body, send, sync, label modify)
    is attempted but the user's Gmail connection status is not "connected".
    """

    status_code = 403
    error_code = "GMAIL_NOT_CONNECTED"
    message = "Gmail is not connected"


class GmailConnectFailedException(GmailError):
    """Gmail OAuth2 connection attempt failed.

    Raised when the OAuth2 callback fails, the user denies Gmail scopes,
    or only a subset of required scopes is granted.
    """

    status_code = 400
    error_code = "GMAIL_CONNECT_FAILED"
    message = "Gmail connection failed"


class GmailFetchError(GmailError):
    """Gmail API call failed when fetching message data.

    Raised when the Gmail API returns an error during message body
    fetch or other read operations after all retries are exhausted.
    """

    status_code = 502
    error_code = "GMAIL_FETCH_ERROR"
    message = "Failed to fetch data from Gmail API"


class MessageNotFoundException(GmailError):
    """Gmail message ID does not exist.

    Raised when a requested Gmail message cannot be found, either
    because the ID is invalid or the message has been deleted.
    """

    status_code = 404
    error_code = "MESSAGE_NOT_FOUND"
    message = "Gmail message not found"


class GmailSendFailedException(GmailError):
    """Email send via Gmail API failed.

    Raised when the Gmail API messages.send call fails after all
    retry attempts (for 5xx errors) or immediately (for non-retryable 4xx).
    """

    status_code = 502
    error_code = "GMAIL_SEND_FAILED"
    message = "Failed to send email via Gmail"


class RateLimitedException(GmailError):
    """Manual sync rate limit exceeded.

    Raised when a user attempts a manual sync within the cooldown
    period (default 30 seconds) of their previous manual sync.
    """

    status_code = 429
    error_code = "RATE_LIMITED"
    message = "Rate limit exceeded, please try again later"

    def __init__(self, message: str | None = None, retry_after: int = 0) -> None:
        """Initialize RateLimitedException.

        Args:
            message: Optional custom message override.
            retry_after: Seconds remaining until the next request is allowed.
        """
        self.retry_after = retry_after
        if message is None and retry_after > 0:
            message = f"Rate limit exceeded, retry after {retry_after} seconds"
        super().__init__(message)


class GmailImportException(GmailError):
    """Historical email import operation failed.

    Raised when the import cannot start (already running, invalid window),
    encounters a permanent error, or the connection is invalid.
    """

    status_code = 409
    error_code = "GMAIL_IMPORT_ERROR"
    message = "Historical email import operation failed"


# ---------------------------------------------------------------------------
# Outbound email exceptions
# ---------------------------------------------------------------------------


class OutboundEmailNotFoundError(GmailError):
    """Outbound email record does not exist.

    Raised when an operation targets an outbound email ID that
    cannot be found in the database.
    """

    status_code = 404
    error_code = "OUTBOUND_EMAIL_NOT_FOUND"
    message = "Outbound email not found"


class OutboundEmailAlreadySentError(GmailError):
    """Outbound email has already been sent.

    Raised when retry is attempted on an already-sent email.
    """

    status_code = 409
    error_code = "OUTBOUND_ALREADY_SENT"
    message = "Outbound email has already been sent"


class OutboundEmailMaxRetriesExceededError(GmailError):
    """Outbound email has exceeded maximum retry attempts.

    Raised when retry is attempted past max_retries.
    """

    status_code = 409
    error_code = "OUTBOUND_MAX_RETRIES"
    message = "Outbound email has exceeded maximum retry attempts"


class OrganizationNotConnectedError(GmailError):
    """Organization Google Connection is not active.

    Raised when sending requires the Organization Google Connection
    but it is not in 'connected' status.
    """

    status_code = 409
    error_code = "ORG_NOT_CONNECTED"
    message = "Organization Google Connection is not active"


class OutboundEmailIdempotencyConflictError(GmailError):
    """Idempotency key already exists with different parameters.

    Raised when creating an outbound email with a duplicate
    idempotency key but different content.
    """

    status_code = 409
    error_code = "OUTBOUND_IDEMPOTENCY_CONFLICT"
    message = "Idempotency key already exists with different content"
