"""Domain-level exceptions."""


class BookChatError(Exception):
    """Base exception for LocalBookChat application."""

    pass


class UnsupportedFileTypeError(BookChatError):
    """Raised when file type is not PDF or EPUB."""

    pass


class FileSizeLimitError(BookChatError):
    """Raised when file exceeds size limit."""

    pass


class BookNotFoundError(BookChatError):
    """Raised when book ID doesn't exist."""

    pass


class LLMConnectionError(BookChatError):
    """Raised when LLM service is unreachable."""

    pass


class SessionLimitError(BookChatError):
    """Raised when session book limit exceeded."""

    pass
