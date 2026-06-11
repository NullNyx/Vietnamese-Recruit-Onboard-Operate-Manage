"""Error handlers for Employee Request module."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.modules.employee_request.domain.exceptions import (
    EmployeeRequestError,
    OvertimeEndBeforeStartError,
    OvertimeOverlapError,
    RequestNotCancellableError,
    RequestNotFoundError,
    RequestNotOwnedByEmployeeError,
)


def register_employee_request_error_handlers(app: FastAPI) -> None:
    """Register error handlers for employee request module exceptions."""

    @app.exception_handler(EmployeeRequestError)
    async def employee_request_error_handler(
        request: Request,
        exc: EmployeeRequestError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(OvertimeEndBeforeStartError)
    async def overtime_end_before_start_handler(
        request: Request,
        exc: OvertimeEndBeforeStartError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(OvertimeOverlapError)
    async def overtime_overlap_handler(
        request: Request,
        exc: OvertimeOverlapError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(RequestNotFoundError)
    async def request_not_found_handler(
        request: Request,
        exc: RequestNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(RequestNotOwnedByEmployeeError)
    async def request_not_owned_handler(
        request: Request,
        exc: RequestNotOwnedByEmployeeError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(RequestNotCancellableError)
    async def request_not_cancellable_handler(
        request: Request,
        exc: RequestNotCancellableError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )
