"""Domain models and exceptions."""

from .book import Book, FileType, VALID_FILE_TYPES
from .chunk import Chunk
from .exceptions import (
    BookChatError,
    BookNotFoundError,
    DocumentParsingError,
    FileSizeLimitError,
    LLMConnectionError,
    SessionLimitError,
    UnsupportedFileTypeError,
)
from .query import QueryRequest, QueryResponse

__all__ = [
    "Book",
    "FileType",
    "VALID_FILE_TYPES",
    "Chunk",
    "QueryRequest",
    "QueryResponse",
    "BookChatError",
    "UnsupportedFileTypeError",
    "FileSizeLimitError",
    "DocumentParsingError",
    "SessionLimitError",
    "BookNotFoundError",
    "LLMConnectionError",
]
