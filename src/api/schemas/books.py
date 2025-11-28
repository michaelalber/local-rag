"""Book-related Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BookResponse(BaseModel):
    """Response schema for a book."""

    id: UUID
    title: str
    author: str | None
    file_type: str
    chunk_count: int

    model_config = ConfigDict(from_attributes=True)
