"""Error handlers for the AI Assistant module."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.modules.assistant.domain.exceptions import (
    AssistantError,
    DraftActionValidationError,
    LLMConnectionError,
    ToolExecutionError,
)
from src.shared.messages import get_message, get_request_language


def register_assistant_error_handlers(app: FastAPI) -> None:
    """Register exception handlers for assistant-related errors."""

    @app.exception_handler(LLMConnectionError)
    async def handle_llm_connection_error(
        request: Request, exc: LLMConnectionError
    ) -> JSONResponse:
        lang = get_request_language(request)
        return JSONResponse(
            status_code=502,
            content={
                "error_code": "ASSISTANT_SERVICE_UNAVAILABLE",
                "detail": get_message("ASSISTANT_SERVICE_UNAVAILABLE", lang),
            },
        )

    @app.exception_handler(ToolExecutionError)
    async def handle_tool_execution_error(
        request: Request, exc: ToolExecutionError
    ) -> JSONResponse:
        lang = get_request_language(request)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "ASSISTANT_ERROR",
                "detail": get_message("ASSISTANT_ERROR", lang),
            },
        )

    @app.exception_handler(DraftActionValidationError)
    async def handle_draft_action_error(
        request: Request, exc: DraftActionValidationError
    ) -> JSONResponse:
        lang = get_request_language(request)
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_ERROR",
                "detail": get_message("VALIDATION_ERROR", lang),
            },
        )

    @app.exception_handler(AssistantError)
    async def handle_assistant_error(request: Request, exc: AssistantError) -> JSONResponse:
        lang = get_request_language(request)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "ASSISTANT_ERROR",
                "detail": get_message("ASSISTANT_ERROR", lang),
            },
        )
