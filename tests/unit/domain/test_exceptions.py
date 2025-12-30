"""Tests for domain exceptions."""

from src.models import (
    BookChatError,
    BookNotFoundError,
    FileSizeLimitError,
    LLMConnectionError,
    UnsupportedFileTypeError,
)


def test_exception_hierarchy():
    """All custom exceptions inherit from BookChatError."""
    assert issubclass(UnsupportedFileTypeError, BookChatError)
    assert issubclass(FileSizeLimitError, BookChatError)
    assert issubclass(BookNotFoundError, BookChatError)
    assert issubclass(LLMConnectionError, BookChatError)


def test_exceptions_carry_message():
    err = UnsupportedFileTypeError("Only PDF and EPUB supported")
    assert str(err) == "Only PDF and EPUB supported"
