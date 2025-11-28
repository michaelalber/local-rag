"""Chat endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header

from src.application.services import QueryService
from src.domain.entities import QueryRequest

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
    Ask a question about loaded books.

    Uses RAG to find relevant context and generate an answer.
    """
    query_request = QueryRequest(
        query=chat_request.query,
        session_id=session_id,
        top_k=chat_request.top_k,
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
            )
            for source in response.sources
        ],
        latency_ms=response.latency_ms,
    )
