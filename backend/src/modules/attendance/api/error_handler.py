"""Error handlers for Attendance module."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.modules.attendance.domain.exceptions import (
    AttendanceError,
    CidrNotFoundError,
    DuplicateCidrError,
    InvalidCidrError,
    OfficeNetworkRequiredError,
    TooManyNetworksError,
)


def register_attendance_error_handlers(app: FastAPI) -> None:
    """Register error handlers for attendance module exceptions."""

    @app.exception_handler(AttendanceError)
    async def attendance_error_handler(
        request: Request,
        exc: AttendanceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(InvalidCidrError)
    async def invalid_cidr_handler(
        request: Request,
        exc: InvalidCidrError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(DuplicateCidrError)
    async def duplicate_cidr_handler(
        request: Request,
        exc: DuplicateCidrError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(TooManyNetworksError)
    async def too_many_networks_handler(
        request: Request,
        exc: TooManyNetworksError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(CidrNotFoundError)
    async def cidr_not_found_handler(
        request: Request,
        exc: CidrNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(OfficeNetworkRequiredError)
    async def office_network_required_handler(
        request: Request,
        exc: OfficeNetworkRequiredError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )
