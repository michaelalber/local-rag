# Phase 6: FastAPI REST Layer

## Objective

Expose application services via REST API with proper validation and error handling.

## Files to Create

```
src/api/
├── __init__.py
├── main.py
├── config.py
├── dependencies.py
├── exception_handlers.py
├── routes/
│   ├── __init__.py
│   ├── books.py
│   ├── chat.py
│   └── health.py
└── schemas/
    ├── __init__.py
    ├── books.py
    └── chat.py
tests/
└── api/
    ├── __init__.py
    ├── conftest.py
    ├── test_books.py
    ├── test_chat.py
    └── test_health.py
```

## Write Tests First

### tests/api/conftest.py

```python
"""API test fixtures."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from uuid import uuid4
from datetime import datetime, UTC

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.api.main import create_app
from src.api.dependencies import (
    get_ingestion_service,
    get_query_service,
    get_session_manager,
    get_vector_store,
)
from src.domain.entities import Book, Chunk, QueryResponse


@pytest.fixture
def sample_book() -> Book:
    return Book(
        id=uuid4(),
        title="Test Book",
        author="Test Author",
        file_path=Path("/uploads/test.pdf"),
        file_type="pdf",
        created_at=datetime.now(UTC),
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
def app(mock_ingestion_service, mock_query_service, mock_session_manager, mock_vector_store):
    """Create test app with mocked dependencies."""
    application = create_app()
    
    application.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion_service
    application.dependency_overrides[get_query_service] = lambda: mock_query_service
    application.dependency_overrides[get_session_manager] = lambda: mock_session_manager
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
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
```

### tests/api/test_health.py

```python
"""Tests for health endpoint."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_check_returns_ok(self, client: TestClient):
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_includes_version(self, client: TestClient):
        response = client.get("/api/health")
        
        data = response.json()
        assert "version" in data
```

### tests/api/test_books.py

```python
"""Tests for book endpoints."""

import pytest
from io import BytesIO
from fastapi.testclient import TestClient

from src.domain.exceptions import SessionLimitError, BookNotFoundError


class TestUploadBooks:
    def test_upload_single_book(self, client: TestClient):
        files = {"files": ("test.pdf", BytesIO(b"fake pdf content"), "application/pdf")}
        
        response = client.post(
            "/api/books",
            files=files,
            headers={"session-id": "test-session"},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Book"

    def test_upload_requires_session_header(self, client: TestClient):
        files = {"files": ("test.pdf", BytesIO(b"content"), "application/pdf")}
        
        response = client.post("/api/books", files=files)
        
        assert response.status_code == 422  # Validation error

    def test_upload_rejects_invalid_file_type(self, client: TestClient, mock_ingestion_service):
        from src.domain.exceptions import UnsupportedFileTypeError
        mock_ingestion_service.ingest_book.side_effect = UnsupportedFileTypeError("Not allowed")
        
        files = {"files": ("test.exe", BytesIO(b"content"), "application/octet-stream")}
        
        response = client.post(
            "/api/books",
            files=files,
            headers={"session-id": "test-session"},
        )
        
        assert response.status_code == 415


class TestListBooks:
    def test_list_books_returns_books(self, client: TestClient):
        response = client.get(
            "/api/books",
            headers={"session-id": "test-session"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Book"

    def test_list_empty_session(self, client: TestClient, mock_session_manager):
        mock_session_manager.get_books.return_value = []
        
        response = client.get(
            "/api/books",
            headers={"session-id": "empty-session"},
        )
        
        assert response.status_code == 200
        assert response.json() == []


class TestDeleteBook:
    def test_delete_book(self, client: TestClient, sample_book):
        response = client.delete(
            f"/api/books/{sample_book.id}",
            headers={"session-id": "test-session"},
        )
        
        assert response.status_code == 204

    def test_delete_nonexistent_book(self, client: TestClient, mock_session_manager):
        from uuid import uuid4
        mock_session_manager.remove_book.side_effect = BookNotFoundError("Not found")
        
        response = client.delete(
            f"/api/books/{uuid4()}",
            headers={"session-id": "test-session"},
        )
        
        assert response.status_code == 404
```

### tests/api/test_chat.py

```python
"""Tests for chat endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.domain.exceptions import LLMConnectionError


class TestChatEndpoint:
    def test_chat_returns_answer(self, client: TestClient):
        response = client.post(
            "/api/chat",
            json={"query": "What is the book about?"},
            headers={"session-id": "test-session"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["answer"] == "This is the answer from the LLM."

    def test_chat_includes_sources(self, client: TestClient):
        response = client.post(
            "/api/chat",
            json={"query": "Question?"},
            headers={"session-id": "test-session"},
        )
        
        data = response.json()
        assert "sources" in data
        assert len(data["sources"]) > 0
        assert "content" in data["sources"][0]
        assert "page_number" in data["sources"][0]

    def test_chat_includes_latency(self, client: TestClient):
        response = client.post(
            "/api/chat",
            json={"query": "Question?"},
            headers={"session-id": "test-session"},
        )
        
        data = response.json()
        assert "latency_ms" in data
        assert data["latency_ms"] > 0

    def test_chat_requires_session_header(self, client: TestClient):
        response = client.post(
            "/api/chat",
            json={"query": "Question?"},
        )
        
        assert response.status_code == 422

    def test_chat_requires_query(self, client: TestClient):
        response = client.post(
            "/api/chat",
            json={},
            headers={"session-id": "test-session"},
        )
        
        assert response.status_code == 422

    def test_chat_handles_llm_error(self, client: TestClient, mock_query_service):
        mock_query_service.query.side_effect = LLMConnectionError("Ollama down")
        
        response = client.post(
            "/api/chat",
            json={"query": "Question?"},
            headers={"session-id": "test-session"},
        )
        
        assert response.status_code == 503
        assert "error" in response.json()
```

## Implementation

### src/api/config.py

```python
"""API configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment."""

    # Paths
    upload_dir: Path = Path("./data/uploads")
    chroma_persist_dir: Path = Path("./data/chroma")

    # Limits
    max_file_size_mb: int = 50
    max_books_per_session: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Models
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "mistral:7b-instruct-q4_K_M"
    ollama_base_url: str = "http://localhost:11434"

    # RAG
    top_k_chunks: int = 5

    # API
    api_prefix: str = "/api"

    class Config:
        env_file = ".env"
        extra = "ignore"


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

### src/api/schemas/books.py

```python
"""Book-related Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel


class BookResponse(BaseModel):
    """Response schema for a book."""

    id: UUID
    title: str
    author: str | None
    file_type: str
    chunk_count: int

    class Config:
        from_attributes = True
```

### src/api/schemas/chat.py

```python
"""Chat-related Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat."""

    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class SourceResponse(BaseModel):
    """Source citation in response."""

    content: str
    page_number: int | None
    chapter: str | None
    book_id: UUID


class ChatResponse(BaseModel):
    """Response schema for chat."""

    answer: str
    sources: list[SourceResponse]
    latency_ms: float | None
```

### src/api/schemas/__init__.py

```python
"""API schemas."""

from .books import BookResponse
from .chat import ChatRequest, ChatResponse, SourceResponse

__all__ = ["BookResponse", "ChatRequest", "ChatResponse", "SourceResponse"]
```

### src/api/dependencies.py

```python
"""FastAPI dependency injection."""

from functools import lru_cache
from pathlib import Path

from src.infrastructure.parsers import get_parser, TextChunker, FileValidator
from src.infrastructure.embeddings import SentenceTransformerEmbedder
from src.infrastructure.vectorstore import ChromaVectorStore
from src.infrastructure.llm import OllamaLLMClient
from src.application.services import SessionManager, BookIngestionService, QueryService
from src.domain.interfaces import VectorStore, EmbeddingService, LLMClient

from .config import Settings, get_settings


@lru_cache
def get_embedder(settings: Settings | None = None) -> EmbeddingService:
    """Get cached embedder instance."""
    settings = settings or get_settings()
    return SentenceTransformerEmbedder(model_name=settings.embedding_model)


@lru_cache
def get_vector_store(settings: Settings | None = None) -> VectorStore:
    """Get cached vector store instance."""
    settings = settings or get_settings()
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    return ChromaVectorStore(persist_dir=settings.chroma_persist_dir)


@lru_cache
def get_llm_client(settings: Settings | None = None) -> LLMClient:
    """Get cached LLM client instance."""
    settings = settings or get_settings()
    return OllamaLLMClient(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
    )


@lru_cache
def get_session_manager(settings: Settings | None = None) -> SessionManager:
    """Get cached session manager instance."""
    settings = settings or get_settings()
    return SessionManager(max_books=settings.max_books_per_session)


def get_ingestion_service(
    settings: Settings | None = None,
) -> BookIngestionService:
    """Get ingestion service with dependencies."""
    settings = settings or get_settings()
    
    return BookIngestionService(
        parser_factory=get_parser,
        chunker=TextChunker(
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        ),
        embedder=get_embedder(settings),
        vector_store=get_vector_store(settings),
        validator=FileValidator(max_size_mb=settings.max_file_size_mb),
    )


def get_query_service(settings: Settings | None = None) -> QueryService:
    """Get query service with dependencies."""
    settings = settings or get_settings()
    
    return QueryService(
        vector_store=get_vector_store(settings),
        embedder=get_embedder(settings),
        llm_client=get_llm_client(settings),
    )
```

### src/api/exception_handlers.py

```python
"""Exception handlers for FastAPI."""

from fastapi import Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    BookChatError,
    UnsupportedFileTypeError,
    FileSizeLimitError,
    BookNotFoundError,
    LLMConnectionError,
    SessionLimitError,
)


async def book_chat_error_handler(request: Request, exc: BookChatError) -> JSONResponse:
    """Handle application-specific errors."""
    status_map = {
        UnsupportedFileTypeError: 415,
        FileSizeLimitError: 413,
        BookNotFoundError: 404,
        LLMConnectionError: 503,
        SessionLimitError: 400,
    }
    
    status_code = status_map.get(type(exc), 500)
    
    return JSONResponse(
        status_code=status_code,
        content={"error": str(exc), "type": type(exc).__name__},
    )
```

### src/api/routes/health.py

```python
"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Check API health."""
    return {
        "status": "ok",
        "version": "0.1.0",
    }
```

### src/api/routes/books.py

```python
"""Book management endpoints."""

from pathlib import Path
from typing import Annotated
from uuid import UUID
import tempfile
import shutil

from fastapi import APIRouter, Depends, Header, UploadFile, File, status

from src.application.services import SessionManager, BookIngestionService
from src.domain.interfaces import VectorStore
from ..dependencies import get_ingestion_service, get_session_manager, get_vector_store
from ..schemas import BookResponse

router = APIRouter(prefix="/books", tags=["books"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=list[BookResponse])
async def upload_books(
    files: Annotated[list[UploadFile], File(...)],
    session_id: Annotated[str, Header()],
    ingestion_service: Annotated[BookIngestionService, Depends(get_ingestion_service)],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> list[BookResponse]:
    """
    Upload one or more books.
    
    Files are validated, parsed, chunked, embedded, and stored.
    """
    books = []
    
    for upload_file in files:
        # Save to temp file
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=Path(upload_file.filename or "file").suffix
        ) as tmp:
            shutil.copyfileobj(upload_file.file, tmp)
            tmp_path = Path(tmp.name)
        
        try:
            # Ingest the book
            book = await ingestion_service.ingest_book(
                file_path=tmp_path,
                session_id=session_id,
            )
            
            # Add to session
            session_manager.add_book(session_id, book)
            
            books.append(BookResponse(
                id=book.id,
                title=book.title,
                author=book.author,
                file_type=book.file_type,
                chunk_count=book.chunk_count,
            ))
        finally:
            # Clean up temp file
            tmp_path.unlink(missing_ok=True)
    
    return books


@router.get("", response_model=list[BookResponse])
async def list_books(
    session_id: Annotated[str, Header()],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> list[BookResponse]:
    """List all books in the current session."""
    books = session_manager.get_books(session_id)
    
    return [
        BookResponse(
            id=book.id,
            title=book.title,
            author=book.author,
            file_type=book.file_type,
            chunk_count=book.chunk_count,
        )
        for book in books
    ]


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: UUID,
    session_id: Annotated[str, Header()],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> None:
    """Remove a book from the session."""
    session_manager.remove_book(session_id, book_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_session(
    session_id: Annotated[str, Header()],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
) -> None:
    """Clear all books from the session."""
    session_manager.clear_session(session_id)
    await vector_store.delete_collection(session_id)
```

### src/api/routes/chat.py

```python
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
    request: ChatRequest,
    session_id: Annotated[str, Header()],
    query_service: Annotated[QueryService, Depends(get_query_service)],
) -> ChatResponse:
    """
    Ask a question about loaded books.
    
    Uses RAG to find relevant context and generate an answer.
    """
    query_request = QueryRequest(
        query=request.query,
        session_id=session_id,
        top_k=request.top_k,
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
```

### src/api/routes/__init__.py

```python
"""API routes."""

from .health import router as health_router
from .books import router as books_router
from .chat import router as chat_router

__all__ = ["health_router", "books_router", "chat_router"]
```

### src/api/main.py

```python
"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.domain.exceptions import BookChatError

from .config import get_settings
from .exception_handlers import book_chat_error_handler
from .routes import health_router, books_router, chat_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="LocalBookChat",
        description="Chat with your eBooks using local LLM",
        version="0.1.0",
    )
    
    # CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handlers
    app.add_exception_handler(BookChatError, book_chat_error_handler)
    
    # Routes
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(books_router, prefix=settings.api_prefix)
    app.include_router(chat_router, prefix=settings.api_prefix)
    
    return app


# Application instance for uvicorn
app = create_app()
```

### src/api/__init__.py

```python
"""API module."""

from .main import create_app, app

__all__ = ["create_app", "app"]
```

## Verification

```bash
# Run API tests
pytest tests/api/ -v

# Run all tests
pytest tests/ -v --ignore=tests/integration

# Start the server
uvicorn src.api.main:app --reload --port 8000

# Test endpoints manually
curl http://localhost:8000/api/health

# Check OpenAPI docs
# Open http://localhost:8000/docs in browser
```

## Commit

```bash
git add .
git commit -m "feat: implement FastAPI REST layer with books and chat endpoints"
```

## Next Phase

Proceed to `docs/phases/PHASE_7_FRONTEND.md`
