"""Exception handlers for FastAPI."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    BookChatError,
    BookNotFoundError,
    DocumentParsingError,
    FileSizeLimitError,
    LLMConnectionError,
    SessionLimitError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)


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
        DocumentParsingError: 422,
    }

    status_code = status_map.get(type(exc), 500)

    return JSONResponse(
        status_code=status_code,
        content={"error": str(exc), "type": type(exc).__name__},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with logging."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__},
    )
