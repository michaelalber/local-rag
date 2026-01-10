"""Chat-related Pydantic schemas."""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class QuerySourceSchema(str, Enum):
    """Query source selection for API."""

    books = "books"
    compliance = "compliance"
    both = "both"


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """Request schema for chat."""

    query: str = Field(..., min_length=1, max_length=2000)
    source: QuerySourceSchema = Field(
        default=QuerySourceSchema.books,
        description="Query source: 'books' (local ebooks), 'compliance' (Aegis MCP), or 'both'",
    )
    top_k: int = Field(default=5, ge=1, le=100, description="Number of chunks to retrieve (deprecated: use retrieval_percentage)")
    retrieval_percentage: float | None = Field(default=2.0, ge=0.5, le=10.0, description="Percentage of chunks to retrieve (0.5-10%)")
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    model: str | None = Field(default=None, description="Ollama model to use (e.g., 'mistral', 'codellama')")


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
