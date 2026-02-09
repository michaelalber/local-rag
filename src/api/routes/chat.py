"""Chat endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header

from src.models import QueryRequest, QuerySource
from src.services import QueryService

from ..dependencies import get_query_service
from ..schemas import ChatRequest, ChatResponse, SourceResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    session_id: Annotated[str, Header()],
    query_service: Annotated[QueryService, Depends(get_query_service)],
) -> ChatResponse:
    """
    Ask a question about loaded books and/or compliance data.

    Uses RAG to find relevant context and generate an answer.
    Source can be 'books', 'compliance', or 'both'.
    """
    # Convert ChatMessage objects to dicts for the domain layer
    conversation_history = None
    if chat_request.history:
        conversation_history = [
            {"role": msg.role, "content": msg.content} for msg in chat_request.history
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

    response = await query_service.query(query_request)

    return ChatResponse(
        answer=response.answer,
        sources=[
            SourceResponse(
                content=source.content,
                page_number=source.page_number,
                chapter=source.chapter,
                book_id=source.book_id,
                has_code=source.has_code,
                code_language=source.code_language,
            )
            for source in response.sources
        ],
        latency_ms=response.latency_ms,
    )
