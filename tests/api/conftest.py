"""API test fixtures."""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from src.api.dependencies import (
    get_ingestion_service,
    get_query_service,
    get_session_manager,
    get_vector_store,
)
from src.api.main import create_app
from src.domain.entities import Book, Chunk, QueryResponse


@pytest.fixture
def sample_book() -> Book:
    return Book(
        id=uuid4(),
        title="Test Book",
        author="Test Author",
        file_path=Path("/uploads/test.pdf"),
        file_type="pdf",
        created_at=datetime.now(timezone.utc),
        chunk_count=10,
    )


@pytest.fixture
def mock_ingestion_service(sample_book):
    service = AsyncMock()
    service.ingest_book.return_value = sample_book
    return service


@pytest.fixture
def mock_query_service():
    service = AsyncMock()
    service.query.return_value = QueryResponse(
        answer="This is the answer from the LLM.",
        sources=[
            Chunk(
                id=uuid4(),
                book_id=uuid4(),
                content="Source content here.",
                page_number=42,
            )
        ],
        latency_ms=150.5,
    )
    return service


@pytest.fixture
def mock_session_manager(sample_book):
    manager = Mock()
    manager.get_books.return_value = [sample_book]
    manager.add_book.return_value = None
    manager.remove_book.return_value = None
    manager.clear_session.return_value = None
    return manager


@pytest.fixture
def mock_vector_store():
    store = AsyncMock()
    store.delete_collection.return_value = None
    return store


@pytest.fixture
def app(
    mock_ingestion_service, mock_query_service, mock_session_manager, mock_vector_store
):
    """Create test app with mocked dependencies."""
    application = create_app()

    application.dependency_overrides[get_ingestion_service] = (
        lambda: mock_ingestion_service
    )
    application.dependency_overrides[get_query_service] = lambda: mock_query_service
    application.dependency_overrides[get_session_manager] = (
        lambda: mock_session_manager
    )
    application.dependency_overrides[get_vector_store] = lambda: mock_vector_store

    return application


@pytest.fixture
def client(app) -> TestClient:
    """Sync test client."""
    return TestClient(app)


@pytest.fixture
async def async_client(app) -> AsyncClient:
    """Async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
