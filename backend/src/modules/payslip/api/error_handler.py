"""Error handlers for Payslip module."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.modules.payslip.domain.exceptions import (
    PayslipError,
    PayslipNotFoundError,
    PayslipNotPublishedError,
)


def register_payslip_error_handlers(app: FastAPI) -> None:
    """Register error handlers for payslip module exceptions."""

    @app.exception_handler(PayslipError)
    async def payslip_error_handler(
        request: Request,
        exc: PayslipError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(PayslipNotFoundError)
    async def payslip_not_found_handler(
        request: Request,
        exc: PayslipNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )

    @app.exception_handler(PayslipNotPublishedError)
    async def payslip_not_published_handler(
        request: Request,
        exc: PayslipNotPublishedError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
            },
        )
