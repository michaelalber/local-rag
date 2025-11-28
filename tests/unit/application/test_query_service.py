"""Tests for query service."""

import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from src.application.services.query_service import QueryService
from src.domain.entities import Chunk, QueryRequest, QueryResponse


class TestQueryService:
    @pytest.fixture
    def mock_vector_store(self):
        store = AsyncMock()
        store.search.return_value = [
            Chunk(
                id=uuid4(),
                book_id=uuid4(),
                content="Relevant content about the topic.",
                page_number=42,
            ),
            Chunk(
                id=uuid4(),
                book_id=uuid4(),
                content="More relevant information.",
                page_number=43,
            ),
        ]
        return store

    @pytest.fixture
    def mock_embedder(self):
        embedder = Mock()
        embedder.embed_query.return_value = [0.1] * 384
        return embedder

    @pytest.fixture
    def mock_llm(self):
        llm = AsyncMock()
        llm.generate.return_value = "The answer based on the context is..."
        return llm

    @pytest.fixture
    def service(self, mock_vector_store, mock_embedder, mock_llm) -> QueryService:
        return QueryService(
            vector_store=mock_vector_store,
            embedder=mock_embedder,
            llm_client=mock_llm,
        )

    @pytest.mark.asyncio
    async def test_query_returns_response_with_answer(self, service: QueryService):
        request = QueryRequest(
            query="What is the main topic?",
            session_id="test-session",
            top_k=5,
        )

        response = await service.query(request)

        assert isinstance(response, QueryResponse)
        assert response.answer == "The answer based on the context is..."

    @pytest.mark.asyncio
    async def test_query_includes_sources(self, service: QueryService):
        request = QueryRequest(query="Question?", session_id="s1", top_k=2)

        response = await service.query(request)

        assert len(response.sources) == 2
        assert all(isinstance(s, Chunk) for s in response.sources)

    @pytest.mark.asyncio
    async def test_query_embeds_question(self, service: QueryService, mock_embedder):
        request = QueryRequest(query="My question?", session_id="s1")

        await service.query(request)

        mock_embedder.embed_query.assert_called_once_with("My question?")

    @pytest.mark.asyncio
    async def test_query_searches_correct_session(
        self, service: QueryService, mock_vector_store
    ):
        request = QueryRequest(query="Q?", session_id="specific-session")

        await service.query(request)

        call_args = mock_vector_store.search.call_args
        assert call_args.kwargs["collection_id"] == "specific-session"

    @pytest.mark.asyncio
    async def test_query_respects_top_k(
        self, service: QueryService, mock_vector_store
    ):
        request = QueryRequest(query="Q?", session_id="s1", top_k=3)

        await service.query(request)

        call_args = mock_vector_store.search.call_args
        assert call_args.kwargs["top_k"] == 3

    @pytest.mark.asyncio
    async def test_query_passes_context_to_llm(self, service: QueryService, mock_llm):
        request = QueryRequest(query="Q?", session_id="s1")

        await service.query(request)

        call_args = mock_llm.generate.call_args
        context = call_args.kwargs["context"]

        assert len(context) == 2
        assert "Relevant content" in context[0]

    @pytest.mark.asyncio
    async def test_query_includes_latency(self, service: QueryService):
        request = QueryRequest(query="Q?", session_id="s1")

        response = await service.query(request)

        assert response.latency_ms is not None
        assert response.latency_ms >= 0
