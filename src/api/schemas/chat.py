"""Chat-related Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """Request schema for chat."""

    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class SourceResponse(BaseModel):
    """Source citation in response."""

    content: str
    page_number: int | None
    chapter: str | None
    book_id: UUID
    has_code: bool = False
    code_language: str | None = None


class ChatResponse(BaseModel):
    """Response schema for chat."""

    answer: str
    sources: list[SourceResponse]
    latency_ms: float | None
