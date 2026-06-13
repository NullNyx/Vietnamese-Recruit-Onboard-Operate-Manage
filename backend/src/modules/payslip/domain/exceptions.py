"""Domain exceptions for the Payslip module."""


class PayslipError(Exception):
    """Base exception for the payslip module."""

    status_code: int = 500
    error_code: str = "PAYSLIP_ERROR"
    message: str = "A payslip module error occurred"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class PayslipNotFoundError(PayslipError):
    """Payslip not found."""

    status_code = 404
    error_code = "PAYSLIP_NOT_FOUND"
    message = "Payslip not found"

    def __init__(self, payslip_id: str) -> None:
        self.message = f"Payslip not found: {payslip_id}"
        super().__init__(self.message)


class PayslipNotPublishedError(PayslipError):
    """Payslip is not published yet."""

    status_code = 403
    error_code = "PAYSLIP_NOT_PUBLISHED"
    message = "Payslip is not yet published"

    def __init__(self, payslip_id: str) -> None:
        self.message = f"Payslip not yet published: {payslip_id}"
        super().__init__(self.message)
