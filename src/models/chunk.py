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
    has_code: bool = False
    code_language: str | None = None
    # Hierarchical chunking fields
    sequence_number: int = 0
    parent_chunk_id: UUID | None = None
    parent_content: str | None = None
