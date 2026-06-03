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


def register_assistant_error_handlers(app: FastAPI) -> None:
    """Register exception handlers for assistant-related errors."""

    @app.exception_handler(LLMConnectionError)
    async def handle_llm_connection_error(
        request: Request, exc: LLMConnectionError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"detail": f"LLM service unavailable: {exc}"},
        )

    @app.exception_handler(ToolExecutionError)
    async def handle_tool_execution_error(
        request: Request, exc: ToolExecutionError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Tool execution failed: {exc}"},
        )

    @app.exception_handler(DraftActionValidationError)
    async def handle_draft_action_error(
        request: Request, exc: DraftActionValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": f"Invalid draft action: {exc}"},
        )

    @app.exception_handler(AssistantError)
    async def handle_assistant_error(
        request: Request, exc: AssistantError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Assistant error: {exc}"},
        )
