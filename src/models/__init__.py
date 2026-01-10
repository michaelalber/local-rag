"""Domain models and exceptions."""

from .book import VALID_FILE_TYPES, Book, FileType
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
from .query import QueryRequest, QueryResponse, QuerySource

__all__ = [
    "Book",
    "FileType",
    "VALID_FILE_TYPES",
    "Chunk",
    "QueryRequest",
    "QueryResponse",
    "QuerySource",
    "BookChatError",
    "UnsupportedFileTypeError",
    "FileSizeLimitError",
    "DocumentParsingError",
    "SessionLimitError",
    "BookNotFoundError",
    "LLMConnectionError",
]
