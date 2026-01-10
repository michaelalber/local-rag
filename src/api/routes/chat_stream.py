"""Streaming chat endpoint using Server-Sent Events."""

import json
import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse

from src.models import Chunk, QueryRequest, QuerySource
from src.services import QueryService

from ..dependencies import get_query_service
from ..schemas import ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def format_sse_event(event: str, data: dict) -> str:
    """Format data as Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def format_sources(chunks: list[Chunk]) -> list[dict]:
    """Format chunks as source dictionaries for SSE."""
    return [
        {
            "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
            "page_number": chunk.page_number,
            "chapter": chunk.chapter,
            "book_id": str(chunk.book_id) if chunk.book_id else None,
        }
        for chunk in chunks
    ]


async def generate_sse_stream(
    query_service: QueryService,
    request: QueryRequest,
) -> AsyncGenerator[str, None]:
    """Generate SSE events for streaming chat response.

    Events:
    - start: Processing started
    - sources: Retrieved sources (books/MCP sources)
    - token: Individual response tokens
    - done: Processing complete
    - error: Error occurred
    """
    try:
        # Event: start
        yield format_sse_event("start", {"status": "processing"})

        # Collect context from selected sources
        source_chunks: list[Chunk] = []  # For attribution
        context_chunks: list[Chunk] = []  # For LLM context
        mcp_context: list[str] = []

        # Determine which sources to query
        book_sources = (QuerySource.BOOKS, QuerySource.BOTH, QuerySource.ALL)
        compliance_sources = (QuerySource.COMPLIANCE, QuerySource.BOTH, QuerySource.ALL)
        query_books = request.source in book_sources
        query_compliance = request.source in compliance_sources
        query_mslearn = request.source in (QuerySource.MSLEARN, QuerySource.ALL)
        query_export_control = request.source in (QuerySource.EXPORT_CONTROL, QuerySource.ALL)

        # Query books if requested
        if query_books:
            source_chunks, context_chunks = await query_service._retrieve_book_chunks(request)

        # Query MCP sources if requested
        if query_compliance:
            compliance_ctx = await query_service._retrieve_mcp_context("compliance", request)
            mcp_context.extend(compliance_ctx)

        if query_mslearn:
            mslearn_ctx = await query_service._retrieve_mcp_context("mslearn", request)
            mcp_context.extend(mslearn_ctx)

        if query_export_control:
            export_ctx = await query_service._retrieve_mcp_context("export_control", request)
            mcp_context.extend(export_ctx)

        # Event: sources (only show original search results, not expanded neighbors)
        sources_data = {
            "book_sources": format_sources(source_chunks),
            "mcp_context_count": len(mcp_context),
        }
        yield format_sse_event("sources", sources_data)

        # Build combined context (use expanded context_chunks for LLM)
        enhanced_chunks = query_service._build_enhanced_chunks(context_chunks)
        combined_context = query_service._combine_context(enhanced_chunks, mcp_context)

        # Stream tokens from LLM
        async for token in query_service.llm_client.generate_stream(
            prompt=request.query,
            context=combined_context,
            conversation_history=request.conversation_history,
            model=request.model,
        ):
            yield format_sse_event("token", {"content": token})

        # Event: done
        yield format_sse_event("done", {"status": "complete"})

    except Exception as e:
        logger.exception("Stream error: %s", e)
        yield format_sse_event("error", {"message": str(e)})


@router.post("/stream")
async def chat_stream(
    chat_request: ChatRequest,
    session_id: Annotated[str, Header()],
    query_service: Annotated[QueryService, Depends(get_query_service)],
) -> StreamingResponse:
    """
    Stream chat responses using Server-Sent Events.

    Returns a stream of SSE events:
    - `start`: Processing has begun
    - `sources`: Retrieved sources from books/compliance
    - `token`: Individual response tokens as they're generated
    - `done`: Processing complete
    - `error`: An error occurred

    Example client usage (JavaScript):
    ```javascript
    const eventSource = new EventSource('/api/chat/stream', {
        method: 'POST',
        body: JSON.stringify({ query: 'What is access control?', source: 'compliance' })
    });

    eventSource.addEventListener('token', (e) => {
        const data = JSON.parse(e.data);
        appendToResponse(data.content);
    });
    ```
    """
    # Convert ChatMessage objects to dicts
    conversation_history = None
    if chat_request.history:
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in chat_request.history
        ]

    # Map schema enum to domain enum
    source = QuerySource(chat_request.source.value)

    query_request = QueryRequest(
        query=chat_request.query,
        session_id=session_id,
        source=source,
        top_k=chat_request.top_k,
        retrieval_percentage=chat_request.retrieval_percentage,
        conversation_history=conversation_history,
        model=chat_request.model,
    )

    return StreamingResponse(
        generate_sse_stream(query_service, query_request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
