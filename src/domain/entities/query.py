"""Query request and response entities."""

from dataclasses import dataclass

from .chunk import Chunk


@dataclass
class QueryRequest:
    """A user query against loaded books."""

    query: str
    session_id: str
    top_k: int = 5
    conversation_history: list[dict[str, str]] | None = None


@dataclass
class QueryResponse:
    """Response to a query with sources."""

    answer: str
    sources: list[Chunk]
    latency_ms: float | None = None
