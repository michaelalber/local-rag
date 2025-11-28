"""Exception handlers for FastAPI."""

from fastapi import Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    BookChatError,
    BookNotFoundError,
    FileSizeLimitError,
    LLMConnectionError,
    SessionLimitError,
    UnsupportedFileTypeError,
)


async def book_chat_error_handler(
    request: Request, exc: BookChatError
) -> JSONResponse:
    """Handle application-specific errors."""
    status_map = {
        UnsupportedFileTypeError: 415,
        FileSizeLimitError: 413,
        BookNotFoundError: 404,
        LLMConnectionError: 503,
        SessionLimitError: 400,
    }

    status_code = status_map.get(type(exc), 500)

    return JSONResponse(
        status_code=status_code,
        content={"error": str(exc), "type": type(exc).__name__},
    )
