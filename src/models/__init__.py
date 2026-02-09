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
    "VALID_FILE_TYPES",
    "Book",
    "BookChatError",
    "BookNotFoundError",
    "Chunk",
    "DocumentParsingError",
    "FileSizeLimitError",
    "FileType",
    "LLMConnectionError",
    "QueryRequest",
    "QueryResponse",
    "QuerySource",
    "SessionLimitError",
    "UnsupportedFileTypeError",
]
