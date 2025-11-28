"""Chunk entity."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class Chunk:
    """A chunk of text from a book for embedding."""

    id: UUID
    book_id: UUID
    content: str
    page_number: int | None = None
    chapter: str | None = None
    embedding: list[float] | None = None
