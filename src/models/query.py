"""Query request and response entities."""

from dataclasses import dataclass
from enum import Enum

from .chunk import Chunk


class QuerySource(str, Enum):
    """Available query sources."""

    BOOKS = "books"
    COMPLIANCE = "compliance"
    MSLEARN = "mslearn"
    EXPORT_CONTROL = "export_control"
    ALL = "all"  # Query all available MCP sources + books

    # Legacy alias for backward compatibility
    BOTH = "both"  # Deprecated: use ALL instead


@dataclass
class QueryRequest:
    """A user query against loaded books and/or compliance data."""

    query: str
    session_id: str
    source: QuerySource = QuerySource.BOOKS
    top_k: int = 5  # Deprecated: use retrieval_percentage instead
    retrieval_percentage: float | None = None  # Percentage of chunks to retrieve (0.5-2.0)
    conversation_history: list[dict[str, str]] | None = None
    model: str | None = None


@dataclass
class QueryResponse:
    """Response to a query with sources."""

    answer: str
    sources: list[Chunk]
    latency_ms: float | None = None
