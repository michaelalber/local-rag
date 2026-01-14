"""Tests for streaming chat endpoint."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.models import Chunk


class TestChatStreamEndpoint:
    """Tests for POST /api/chat/stream endpoint."""

    @pytest.fixture
    def mock_query_service_streaming(self):
        """Create mock query service with streaming support."""
        service = MagicMock()

        # Mock _retrieve_book_chunks - returns (source_chunks, context_chunks)
        mock_chunks = [
            Chunk(
                id=uuid4(),
                book_id=uuid4(),
                content="Test chunk content about access control.",
                page_number=1,
                chapter="Chapter 1",
            )
        ]
        service._retrieve_book_chunks = AsyncMock(return_value=(mock_chunks, mock_chunks))

        # Mock _retrieve_compliance_context
        service._retrieve_compliance_context = AsyncMock(return_value=[])

        # Mock _build_enhanced_chunks to return same chunks
        service._build_enhanced_chunks = MagicMock(side_effect=lambda x: x)

        # Mock _combine_context
        service._combine_context = MagicMock(
            side_effect=lambda chunks, compliance: chunks if not compliance else compliance
        )

        # Mock llm_client.generate_stream to yield tokens
        async def mock_generate_stream(*args, **kwargs):
            tokens = ["This ", "is ", "a ", "test ", "response."]
            for token in tokens:
                yield token

        service.llm_client = MagicMock()
        service.llm_client.generate_stream = mock_generate_stream

        return service

    @pytest.mark.asyncio
    async def test_stream_returns_sse_content_type(
        self, app, mock_query_service_streaming
    ):
        """Test that streaming endpoint returns SSE content type."""
        from src.api.dependencies import get_aegis_client, get_query_service

        async def override():
            return mock_query_service_streaming

        async def override_aegis():
            return None

        app.dependency_overrides[get_query_service] = override
        app.dependency_overrides[get_aegis_client] = override_aegis

        from httpx import ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/chat/stream",
                json={"query": "What is access control?"},
                headers={"session-id": "test-session"},
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    @pytest.mark.asyncio
    async def test_stream_returns_start_event(self, app, mock_query_service_streaming):
        """Test that stream starts with start event."""
        from src.api.dependencies import get_aegis_client, get_query_service

        async def override():
            return mock_query_service_streaming

        async def override_aegis():
            return None

        app.dependency_overrides[get_query_service] = override
        app.dependency_overrides[get_aegis_client] = override_aegis

        from httpx import ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/chat/stream",
                json={"query": "What is access control?"},
                headers={"session-id": "test-session"},
            )

        assert response.status_code == 200
        content = response.text
        assert "event: start" in content
        assert '"status": "processing"' in content

    @pytest.mark.asyncio
    async def test_stream_returns_sources_event(self, app, mock_query_service_streaming):
        """Test that stream includes sources event."""
        from src.api.dependencies import get_aegis_client, get_query_service

        async def override():
            return mock_query_service_streaming

        async def override_aegis():
            return None

        app.dependency_overrides[get_query_service] = override
        app.dependency_overrides[get_aegis_client] = override_aegis

        from httpx import ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/chat/stream",
                json={"query": "What is access control?"},
                headers={"session-id": "test-session"},
            )

        assert response.status_code == 200
        content = response.text
        assert "event: sources" in content

    @pytest.mark.asyncio
    async def test_stream_returns_token_events(self, app, mock_query_service_streaming):
        """Test that stream includes token events."""
        from src.api.dependencies import get_aegis_client, get_query_service

        async def override():
            return mock_query_service_streaming

        async def override_aegis():
            return None

        app.dependency_overrides[get_query_service] = override
        app.dependency_overrides[get_aegis_client] = override_aegis

        from httpx import ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/chat/stream",
                json={"query": "What is access control?"},
                headers={"session-id": "test-session"},
            )

        assert response.status_code == 200
        content = response.text
        assert "event: token" in content

    @pytest.mark.asyncio
    async def test_stream_returns_done_event(self, app, mock_query_service_streaming):
        """Test that stream ends with done event."""
        from src.api.dependencies import get_aegis_client, get_query_service

        async def override():
            return mock_query_service_streaming

        async def override_aegis():
            return None

        app.dependency_overrides[get_query_service] = override
        app.dependency_overrides[get_aegis_client] = override_aegis

        from httpx import ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/chat/stream",
                json={"query": "What is access control?"},
                headers={"session-id": "test-session"},
            )

        assert response.status_code == 200
        content = response.text
        assert "event: done" in content
        assert '"status": "complete"' in content

    @pytest.mark.asyncio
    async def test_stream_with_source_books(self, app, mock_query_service_streaming):
        """Test streaming with books source."""
        from src.api.dependencies import get_aegis_client, get_query_service

        async def override():
            return mock_query_service_streaming

        async def override_aegis():
            return None

        app.dependency_overrides[get_query_service] = override
        app.dependency_overrides[get_aegis_client] = override_aegis

        from httpx import ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/chat/stream",
                json={"query": "What is in chapter 1?", "source": "books"},
                headers={"session-id": "test-session"},
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_stream_with_source_compliance(self, app, mock_query_service_streaming):
        """Test streaming with compliance source."""
        from src.api.dependencies import get_aegis_client, get_query_service

        async def override():
            return mock_query_service_streaming

        async def override_aegis():
            return None

        app.dependency_overrides[get_query_service] = override
        app.dependency_overrides[get_aegis_client] = override_aegis

        from httpx import ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/chat/stream",
                json={"query": "NIST password requirements?", "source": "compliance"},
                headers={"session-id": "test-session"},
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_stream_requires_session_id(self, app, mock_query_service_streaming):
        """Test that session-id header is required."""
        from src.api.dependencies import get_aegis_client, get_query_service

        async def override():
            return mock_query_service_streaming

        async def override_aegis():
            return None

        app.dependency_overrides[get_query_service] = override
        app.dependency_overrides[get_aegis_client] = override_aegis

        from httpx import ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/chat/stream",
                json={"query": "Test question?"},
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_stream_validates_query(self, app, mock_query_service_streaming):
        """Test that empty query is rejected."""
        from src.api.dependencies import get_aegis_client, get_query_service

        async def override():
            return mock_query_service_streaming

        async def override_aegis():
            return None

        app.dependency_overrides[get_query_service] = override
        app.dependency_overrides[get_aegis_client] = override_aegis

        from httpx import ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/chat/stream",
                json={"query": ""},
                headers={"session-id": "test-session"},
            )

        assert response.status_code == 422
