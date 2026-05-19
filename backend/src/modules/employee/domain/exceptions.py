"""Domain exceptions for the Employee Management module.

This module defines the exception hierarchy used throughout the employee
module to represent business rule violations and resource errors.
"""


class EmployeeError(Exception):
    """Base exception for the employee module.

    All domain-specific exceptions inherit from this class, enabling
    a single exception handler to catch any employee-related error and
    return a consistent JSON error response.

    Attributes:
        status_code: HTTP status code to return to the client.
        error_code: Machine-readable error identifier.
        message: Human-readable error description.
    """

    status_code: int = 500
    error_code: str = "EMPLOYEE_ERROR"
    message: str = "An employee module error occurred"

    def __init__(self, message: str | None = None) -> None:
        """Initialize EmployeeError.

        Args:
            message: Optional custom message override. If not provided,
                the class-level default message is used.
        """
        if message is not None:
            self.message = message
        super().__init__(self.message)


class DuplicateEmailError(EmployeeError):
    """Employee email already exists in the system.

    Raised when attempting to create or update an employee with an
    email address that is already assigned to another employee record.
    """

    status_code = 409
    error_code = "EMPLOYEE_DUPLICATE_EMAIL"
    message = "Employee with this email already exists"


class EmployeeNotFoundError(EmployeeError):
    """Requested employee does not exist.

    Raised when an operation targets an employee ID that cannot be
    found in the database.
    """

    status_code = 404
    error_code = "EMPLOYEE_NOT_FOUND"
    message = "Employee not found"


class DepartmentNotFoundError(EmployeeError):
    """Requested department does not exist.

    Raised when an operation references a department ID that cannot
    be found in the database.
    """

    status_code = 404
    error_code = "DEPARTMENT_NOT_FOUND"
    message = "Department not found"


class PositionNotFoundError(EmployeeError):
    """Requested position does not exist.

    Raised when an operation references a position ID that cannot
    be found in the database.
    """

    status_code = 404
    error_code = "POSITION_NOT_FOUND"
    message = "Position not found"


class DepartmentHasEmployeesError(EmployeeError):
    """Department cannot be deleted because it has active employees.

    Raised when attempting to delete a department that still has
    employees assigned to it.
    """

    status_code = 409
    error_code = "DEPARTMENT_HAS_EMPLOYEES"
    message = "Cannot delete department with active employees"


class PositionHasEmployeesError(EmployeeError):
    """Position cannot be deleted because it has active employees.

    Raised when attempting to delete a position that still has
    employees assigned to it.
    """

    status_code = 409
    error_code = "POSITION_HAS_EMPLOYEES"
    message = "Cannot delete position with active employees"


class FileTooLargeError(EmployeeError):
    """Uploaded file exceeds the maximum allowed size.

    Raised when a document upload exceeds the 10MB size limit.
    """

    status_code = 413
    error_code = "FILE_TOO_LARGE"
    message = "File exceeds maximum size of 10MB"


class UnsupportedFileTypeError(EmployeeError):
    """Uploaded file has an unsupported MIME type.

    Raised when a document upload uses a file type that is not
    in the list of accepted MIME types.
    """

    status_code = 415
    error_code = "UNSUPPORTED_FILE_TYPE"
    message = "File type not supported"
