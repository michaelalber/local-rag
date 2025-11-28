# Phase 5: Application Services

## Objective

Implement use case orchestration: book ingestion, querying, and session management.

## Files to Create

```
src/application/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── ingestion_service.py
│   ├── query_service.py
│   └── session_manager.py
└── dto/
    ├── __init__.py
    └── responses.py
tests/unit/application/
├── __init__.py
├── test_ingestion_service.py
├── test_query_service.py
└── test_session_manager.py
```

## Write Tests First

### tests/unit/application/test_session_manager.py

```python
"""Tests for session manager."""

import pytest
from uuid import uuid4
from datetime import datetime, UTC
from pathlib import Path

from src.domain.entities import Book
from src.domain.exceptions import SessionLimitError, BookNotFoundError
from src.application.services.session_manager import SessionManager


class TestSessionManager:
    @pytest.fixture
    def manager(self) -> SessionManager:
        return SessionManager(max_books=3)

    @pytest.fixture
    def sample_book(self) -> Book:
        return Book(
            id=uuid4(),
            title="Test Book",
            author="Test Author",
            file_path=Path("/uploads/test.pdf"),
            file_type="pdf",
            created_at=datetime.now(UTC),
        )

    def test_add_book_to_session(self, manager: SessionManager, sample_book: Book):
        session_id = "session-1"
        manager.add_book(session_id, sample_book)
        
        books = manager.get_books(session_id)
        assert len(books) == 1
        assert books[0].id == sample_book.id

    def test_get_books_empty_session(self, manager: SessionManager):
        books = manager.get_books("nonexistent")
        assert books == []

    def test_session_limit_enforced(self, manager: SessionManager):
        session_id = "limited-session"
        
        # Add max books
        for i in range(3):
            book = Book(
                id=uuid4(),
                title=f"Book {i}",
                author=None,
                file_path=Path(f"/uploads/book{i}.pdf"),
                file_type="pdf",
                created_at=datetime.now(UTC),
            )
            manager.add_book(session_id, book)
        
        # Fourth should fail
        extra_book = Book(
            id=uuid4(),
            title="Extra Book",
            author=None,
            file_path=Path("/uploads/extra.pdf"),
            file_type="pdf",
            created_at=datetime.now(UTC),
        )
        
        with pytest.raises(SessionLimitError):
            manager.add_book(session_id, extra_book)

    def test_remove_book(self, manager: SessionManager, sample_book: Book):
        session_id = "session-1"
        manager.add_book(session_id, sample_book)
        
        manager.remove_book(session_id, sample_book.id)
        
        assert manager.get_books(session_id) == []

    def test_remove_nonexistent_book(self, manager: SessionManager):
        with pytest.raises(BookNotFoundError):
            manager.remove_book("session-1", uuid4())

    def test_clear_session(self, manager: SessionManager, sample_book: Book):
        session_id = "session-1"
        manager.add_book(session_id, sample_book)
        
        manager.clear_session(session_id)
        
        assert manager.get_books(session_id) == []

    def test_sessions_are_isolated(self, manager: SessionManager):
        book1 = Book(
            id=uuid4(), title="Book 1", author=None,
            file_path=Path("/b1.pdf"), file_type="pdf", created_at=datetime.now(UTC)
        )
        book2 = Book(
            id=uuid4(), title="Book 2", author=None,
            file_path=Path("/b2.pdf"), file_type="pdf", created_at=datetime.now(UTC)
        )
        
        manager.add_book("session-a", book1)
        manager.add_book("session-b", book2)
        
        assert len(manager.get_books("session-a")) == 1
        assert manager.get_books("session-a")[0].title == "Book 1"
        assert len(manager.get_books("session-b")) == 1
        assert manager.get_books("session-b")[0].title == "Book 2"
```

### tests/unit/application/test_ingestion_service.py

```python
"""Tests for book ingestion service."""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from uuid import uuid4
from pathlib import Path

from src.domain.entities import Book, Chunk
from src.application.services.ingestion_service import BookIngestionService


class TestBookIngestionService:
    @pytest.fixture
    def mock_parser(self):
        parser = Mock()
        parser.parse.return_value = ("Test Title", "Test Author")
        parser.extract_text.return_value = [
            ("Page 1 content here.", {"page_number": 1}),
            ("Page 2 content here.", {"page_number": 2}),
        ]
        return parser

    @pytest.fixture
    def mock_parser_factory(self, mock_parser):
        return Mock(return_value=mock_parser)

    @pytest.fixture
    def mock_chunker(self):
        chunker = Mock()
        chunker.chunk.return_value = [
            {"text": "Chunk 1", "metadata": {"page_number": 1}},
            {"text": "Chunk 2", "metadata": {"page_number": 1}},
        ]
        return chunker

    @pytest.fixture
    def mock_embedder(self):
        embedder = Mock()
        embedder.embed.return_value = [[0.1] * 384, [0.2] * 384]
        return embedder

    @pytest.fixture
    def mock_vector_store(self):
        store = AsyncMock()
        return store

    @pytest.fixture
    def mock_validator(self):
        validator = Mock()
        validator.validate_file.return_value = "safe_filename.pdf"
        return validator

    @pytest.fixture
    def service(
        self,
        mock_parser_factory,
        mock_chunker,
        mock_embedder,
        mock_vector_store,
        mock_validator,
    ) -> BookIngestionService:
        return BookIngestionService(
            parser_factory=mock_parser_factory,
            chunker=mock_chunker,
            embedder=mock_embedder,
            vector_store=mock_vector_store,
            validator=mock_validator,
        )

    @pytest.mark.asyncio
    async def test_ingest_book_returns_book_entity(
        self, service: BookIngestionService, tmp_path: Path
    ):
        # Create a dummy file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake pdf content")
        
        book = await service.ingest_book(
            file_path=test_file,
            session_id="test-session",
        )
        
        assert isinstance(book, Book)
        assert book.title == "Test Title"
        assert book.author == "Test Author"

    @pytest.mark.asyncio
    async def test_ingest_stores_chunks_in_vector_store(
        self, service: BookIngestionService, mock_vector_store, tmp_path: Path
    ):
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake pdf content")
        
        await service.ingest_book(file_path=test_file, session_id="test-session")
        
        # Vector store should have been called with chunks
        mock_vector_store.add_chunks.assert_called_once()
        call_args = mock_vector_store.add_chunks.call_args
        chunks = call_args[0][0]  # First positional arg
        
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)

    @pytest.mark.asyncio
    async def test_ingest_validates_file(
        self, service: BookIngestionService, mock_validator, tmp_path: Path
    ):
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"content")
        
        await service.ingest_book(file_path=test_file, session_id="s1")
        
        mock_validator.validate_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_book_has_correct_chunk_count(
        self, service: BookIngestionService, mock_chunker, tmp_path: Path
    ):
        # Mock returns 2 chunks per page, 2 pages = 4 total
        mock_chunker.chunk.return_value = [
            {"text": "C1", "metadata": {}},
            {"text": "C2", "metadata": {}},
        ]
        
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"content")
        
        book = await service.ingest_book(file_path=test_file, session_id="s1")
        
        # 2 pages × 2 chunks each
        assert book.chunk_count == 4
```

### tests/unit/application/test_query_service.py

```python
"""Tests for query service."""

import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from src.domain.entities import Chunk, QueryRequest, QueryResponse
from src.application.services.query_service import QueryService


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
    async def test_query_embeds_question(
        self, service: QueryService, mock_embedder
    ):
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
    async def test_query_passes_context_to_llm(
        self, service: QueryService, mock_llm
    ):
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
```

## Implementation

### src/application/services/session_manager.py

```python
"""Session management for loaded books."""

from uuid import UUID

from src.domain.entities import Book
from src.domain.exceptions import SessionLimitError, BookNotFoundError


class SessionManager:
    """Manages book sessions with limits."""

    def __init__(self, max_books: int = 5):
        """
        Args:
            max_books: Maximum books per session.
        """
        self.max_books = max_books
        self._sessions: dict[str, list[Book]] = {}

    def add_book(self, session_id: str, book: Book) -> None:
        """
        Add a book to a session.

        Raises:
            SessionLimitError: If session is at max capacity.
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        if len(self._sessions[session_id]) >= self.max_books:
            raise SessionLimitError(
                f"Session limit of {self.max_books} books reached. "
                "Remove a book before adding more."
            )

        self._sessions[session_id].append(book)

    def get_books(self, session_id: str) -> list[Book]:
        """Get all books in a session."""
        return self._sessions.get(session_id, []).copy()

    def get_book(self, session_id: str, book_id: UUID) -> Book:
        """
        Get a specific book.

        Raises:
            BookNotFoundError: If book not found.
        """
        books = self._sessions.get(session_id, [])
        for book in books:
            if book.id == book_id:
                return book
        raise BookNotFoundError(f"Book {book_id} not found in session {session_id}")

    def remove_book(self, session_id: str, book_id: UUID) -> None:
        """
        Remove a book from a session.

        Raises:
            BookNotFoundError: If book not found.
        """
        books = self._sessions.get(session_id, [])
        for i, book in enumerate(books):
            if book.id == book_id:
                del books[i]
                return
        raise BookNotFoundError(f"Book {book_id} not found in session {session_id}")

    def clear_session(self, session_id: str) -> None:
        """Remove all books from a session."""
        self._sessions.pop(session_id, None)

    def session_exists(self, session_id: str) -> bool:
        """Check if session has any books."""
        return session_id in self._sessions and len(self._sessions[session_id]) > 0
```

### src/application/services/ingestion_service.py

```python
"""Book ingestion service."""

from datetime import datetime, UTC
from pathlib import Path
from typing import Callable
from uuid import uuid4

from src.domain.entities import Book, Chunk
from src.domain.interfaces import DocumentParser, EmbeddingService, VectorStore
from src.infrastructure.parsers import FileValidator, TextChunker


class BookIngestionService:
    """Orchestrates book ingestion: parse, chunk, embed, store."""

    def __init__(
        self,
        parser_factory: Callable[[Path], DocumentParser],
        chunker: TextChunker,
        embedder: EmbeddingService,
        vector_store: VectorStore,
        validator: FileValidator,
    ):
        """
        Args:
            parser_factory: Factory function that returns parser for a file path.
            chunker: Text chunking service.
            embedder: Embedding service.
            vector_store: Vector storage.
            validator: File validator.
        """
        self.parser_factory = parser_factory
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.validator = validator

    async def ingest_book(self, file_path: Path, session_id: str) -> Book:
        """
        Ingest a book: validate, parse, chunk, embed, and store.

        Args:
            file_path: Path to the book file.
            session_id: Session identifier for vector storage.

        Returns:
            Book entity with metadata.

        Raises:
            UnsupportedFileTypeError: If file type not supported.
            FileSizeLimitError: If file too large.
        """
        # Validate
        file_size = file_path.stat().st_size
        self.validator.validate_file(file_path, file_size)

        # Parse
        parser = self.parser_factory(file_path)
        title, author = parser.parse(file_path)
        text_segments = parser.extract_text(file_path)

        # Chunk all segments
        all_chunks_data = []
        for text, metadata in text_segments:
            chunk_dicts = self.chunker.chunk(text, metadata)
            all_chunks_data.extend(chunk_dicts)

        # Create book entity
        book_id = uuid4()
        book = Book(
            id=book_id,
            title=title,
            author=author,
            file_path=file_path,
            file_type=file_path.suffix.lstrip(".").lower(),  # type: ignore
            created_at=datetime.now(UTC),
            chunk_count=len(all_chunks_data),
        )

        # Embed chunks
        texts = [c["text"] for c in all_chunks_data]
        embeddings = self.embedder.embed(texts)

        # Create Chunk entities
        chunks = []
        for chunk_data, embedding in zip(all_chunks_data, embeddings):
            chunk = Chunk(
                id=uuid4(),
                book_id=book_id,
                content=chunk_data["text"],
                page_number=chunk_data["metadata"].get("page_number"),
                chapter=chunk_data["metadata"].get("chapter"),
                embedding=embedding,
            )
            chunks.append(chunk)

        # Store in vector database
        await self.vector_store.add_chunks(chunks, session_id)

        return book
```

### src/application/services/query_service.py

```python
"""Query service for RAG-based question answering."""

import time

from src.domain.entities import QueryRequest, QueryResponse
from src.domain.interfaces import VectorStore, EmbeddingService, LLMClient


class QueryService:
    """Handles RAG queries against loaded books."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: EmbeddingService,
        llm_client: LLMClient,
    ):
        """
        Args:
            vector_store: Vector storage for retrieval.
            embedder: Embedding service for query.
            llm_client: LLM for generation.
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm_client = llm_client

    async def query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a RAG query.

        Args:
            request: Query request with question and session.

        Returns:
            Response with answer and sources.
        """
        start_time = time.perf_counter()

        # Embed the query
        query_embedding = self.embedder.embed_query(request.query)

        # Retrieve relevant chunks
        chunks = await self.vector_store.search(
            query_embedding=query_embedding,
            collection_id=request.session_id,
            top_k=request.top_k,
        )

        # Build context from chunks
        context = [chunk.content for chunk in chunks]

        # Generate answer
        answer = await self.llm_client.generate(
            prompt=request.query,
            context=context,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return QueryResponse(
            answer=answer,
            sources=chunks,
            latency_ms=elapsed_ms,
        )
```

### src/application/services/__init__.py

```python
"""Application services."""

from .session_manager import SessionManager
from .ingestion_service import BookIngestionService
from .query_service import QueryService

__all__ = ["SessionManager", "BookIngestionService", "QueryService"]
```

### src/application/dto/responses.py

```python
"""Data transfer objects for API responses."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class BookDTO:
    """Book data for API responses."""

    id: UUID
    title: str
    author: str | None
    file_type: str
    chunk_count: int


@dataclass  
class SourceDTO:
    """Source citation for query responses."""

    content: str
    page_number: int | None
    chapter: str | None
    book_id: UUID


@dataclass
class ChatResponseDTO:
    """Chat response for API."""

    answer: str
    sources: list[SourceDTO]
    latency_ms: float | None
```

### src/application/dto/__init__.py

```python
"""Application DTOs."""

from .responses import BookDTO, SourceDTO, ChatResponseDTO

__all__ = ["BookDTO", "SourceDTO", "ChatResponseDTO"]
```

### src/application/__init__.py

```python
"""Application layer."""

from .services import SessionManager, BookIngestionService, QueryService
from .dto import BookDTO, SourceDTO, ChatResponseDTO

__all__ = [
    "SessionManager",
    "BookIngestionService", 
    "QueryService",
    "BookDTO",
    "SourceDTO",
    "ChatResponseDTO",
]
```

## Verification

```bash
# Run application service tests
pytest tests/unit/application/ -v

# All tests should pass
pytest tests/ -v --ignore=tests/integration

# Quick integration test (manual)
python -c "
import asyncio
from pathlib import Path
from src.infrastructure.parsers import get_parser, TextChunker, FileValidator
from src.infrastructure.embeddings import SentenceTransformerEmbedder
from src.infrastructure.vectorstore import ChromaVectorStore
from src.infrastructure.llm import OllamaLLMClient
from src.application.services import BookIngestionService, QueryService, SessionManager
from src.domain.entities import QueryRequest

async def test():
    # Setup
    embedder = SentenceTransformerEmbedder()
    store = ChromaVectorStore(Path('./data/chroma'))
    llm = OllamaLLMClient()
    
    if not await llm.health_check():
        print('Ollama not running, skipping LLM test')
        return
    
    ingestion = BookIngestionService(
        parser_factory=get_parser,
        chunker=TextChunker(),
        embedder=embedder,
        vector_store=store,
        validator=FileValidator(),
    )
    
    query_service = QueryService(
        vector_store=store,
        embedder=embedder,
        llm_client=llm,
    )
    
    session = SessionManager()
    
    # Test with a real book (update path)
    # book = await ingestion.ingest_book(Path('path/to/book.pdf'), 'test-session')
    # session.add_book('test-session', book)
    
    # response = await query_service.query(QueryRequest(
    #     query='What is this book about?',
    #     session_id='test-session'
    # ))
    # print(f'Answer: {response.answer}')
    
    print('Services initialized successfully!')

asyncio.run(test())
"
```

## Commit

```bash
git add .
git commit -m "feat: implement application services for ingestion, query, and sessions"
```

## Next Phase

Proceed to `docs/phases/PHASE_6_API.md`
