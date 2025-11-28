"""Data transfer objects for API responses."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class BookDTO:
    """Book data for API responses."""

    id: UUID
    title: str
    author: str | None
    file_type: str
    chunk_count: int


@dataclass
class SourceDTO:
    """Source citation for query responses."""

    content: str
    page_number: int | None
    chapter: str | None
    book_id: UUID


@dataclass
class ChatResponseDTO:
    """Chat response for API."""

    answer: str
    sources: list[SourceDTO]
    latency_ms: float | None
