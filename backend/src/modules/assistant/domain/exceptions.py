"""Domain exceptions for the AI Assistant module."""


class AssistantError(Exception):
    """Base exception for assistant-related errors."""


class LLMConnectionError(AssistantError):
    """Raised when the LLM endpoint is unreachable."""


class ToolExecutionError(AssistantError):
    """Raised when a Read-Tool fails to execute."""


class DraftActionValidationError(AssistantError):
    """Raised when a Draft-Tool returns invalid data."""
