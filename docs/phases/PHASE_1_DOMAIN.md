# Phase 1: Domain Layer

## Objective

Define core entities and interfaces. Pure Python only—no external dependencies except stdlib.

## Files to Create

```
src/domain/
├── entities/
│   ├── __init__.py
│   ├── book.py
│   ├── chunk.py
│   └── query.py
├── interfaces/
│   ├── __init__.py
│   ├── document_parser.py
│   ├── embedding_service.py
│   ├── vector_store.py
│   └── llm_client.py
└── exceptions.py  (extend existing)
```

## Write Tests First

Create `tests/unit/domain/` directory and write these tests before implementing:

### tests/unit/domain/test_entities.py

```python
"""Tests for domain entities."""

import pytest
from uuid import uuid4
from datetime import datetime, UTC
from pathlib import Path

from src.domain.entities import Book, Chunk, QueryRequest, QueryResponse


class TestBook:
    def test_create_book_with_valid_pdf(self):
        book = Book(
            id=uuid4(),
            title="Test Book",
            author="Test Author",
            file_path=Path("/uploads/test.pdf"),
            file_type="pdf",
            created_at=datetime.now(UTC),
        )
        assert book.file_type == "pdf"
        assert book.chunk_count == 0

    def test_create_book_with_valid_epub(self):
        book = Book(
            id=uuid4(),
            title="Test Book",
            author=None,
            file_path=Path("/uploads/test.epub"),
            file_type="epub",
            created_at=datetime.now(UTC),
        )
        assert book.file_type == "epub"

    def test_book_rejects_invalid_file_type(self):
        with pytest.raises(ValueError, match="file_type"):
            Book(
                id=uuid4(),
                title="Test",
                author=None,
                file_path=Path("/test.doc"),
                file_type="doc",
                created_at=datetime.now(UTC),
            )


class TestChunk:
    def test_create_chunk_with_metadata(self):
        chunk = Chunk(
            id=uuid4(),
            book_id=uuid4(),
            content="This is sample content from the book.",
            page_number=42,
            chapter="Chapter 3",
        )
        assert chunk.page_number == 42
        assert chunk.embedding is None

    def test_chunk_with_embedding(self):
        embedding = [0.1, 0.2, 0.3]
        chunk = Chunk(
            id=uuid4(),
            book_id=uuid4(),
            content="Content",
            page_number=1,
            embedding=embedding,
        )
        assert chunk.embedding == embedding


class TestQueryRequest:
    def test_create_query_request(self):
        request = QueryRequest(
            query="What is the main theme?",
            session_id="session-123",
            top_k=5,
        )
        assert request.top_k == 5

    def test_query_request_default_top_k(self):
        request = QueryRequest(query="Question", session_id="s1")
        assert request.top_k == 5  # default


class TestQueryResponse:
    def test_create_response_with_sources(self):
        chunk = Chunk(
            id=uuid4(),
            book_id=uuid4(),
            content="Source content",
            page_number=10,
        )
        response = QueryResponse(
            answer="The answer is...",
            sources=[chunk],
            latency_ms=150.5,
        )
        assert len(response.sources) == 1
        assert response.latency_ms == 150.5
```

### tests/unit/domain/test_exceptions.py

```python
"""Tests for domain exceptions."""

from src.domain.exceptions import (
    BookChatError,
    UnsupportedFileTypeError,
    FileSizeLimitError,
    BookNotFoundError,
    LLMConnectionError,
)


def test_exception_hierarchy():
    """All custom exceptions inherit from BookChatError."""
    assert issubclass(UnsupportedFileTypeError, BookChatError)
    assert issubclass(FileSizeLimitError, BookChatError)
    assert issubclass(BookNotFoundError, BookChatError)
    assert issubclass(LLMConnectionError, BookChatError)


def test_exceptions_carry_message():
    err = UnsupportedFileTypeError("Only PDF and EPUB supported")
    assert str(err) == "Only PDF and EPUB supported"
```

## Implementation

### src/domain/entities/book.py

```python
"""Book entity."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import UUID


@dataclass
class Book:
    """Represents an uploaded book."""

    id: UUID
    title: str
    file_path: Path
    file_type: Literal["pdf", "epub"]
    created_at: datetime
    author: str | None = None
    chunk_count: int = 0

    def __post_init__(self) -> None:
        if self.file_type not in ("pdf", "epub"):
            raise ValueError(f"Invalid file_type: {self.file_type}. Must be 'pdf' or 'epub'.")
```

### src/domain/entities/chunk.py

```python
"""Chunk entity."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class Chunk:
    """A chunk of text from a book for embedding."""

    id: UUID
    book_id: UUID
    content: str
    page_number: int | None = None
    chapter: str | None = None
    embedding: list[float] | None = None
```

### src/domain/entities/query.py

```python
"""Query request and response entities."""

from dataclasses import dataclass, field

from .chunk import Chunk


@dataclass
class QueryRequest:
    """A user query against loaded books."""

    query: str
    session_id: str
    top_k: int = 5


@dataclass
class QueryResponse:
    """Response to a query with sources."""

    answer: str
    sources: list[Chunk]
    latency_ms: float | None = None
```

### src/domain/entities/__init__.py

```python
"""Domain entities."""

from .book import Book
from .chunk import Chunk
from .query import QueryRequest, QueryResponse

__all__ = ["Book", "Chunk", "QueryRequest", "QueryResponse"]
```

### src/domain/interfaces/document_parser.py

```python
"""Document parser interface."""

from abc import ABC, abstractmethod
from pathlib import Path

from ..entities import Book, Chunk


class DocumentParser(ABC):
    """Interface for parsing documents into chunks."""

    @abstractmethod
    def parse(self, file_path: Path) -> tuple[str, str | None]:
        """
        Parse document and extract metadata.

        Returns:
            Tuple of (title, author). Author may be None.
        """
        pass

    @abstractmethod
    def extract_text(self, file_path: Path) -> list[tuple[str, dict]]:
        """
        Extract text with metadata.

        Returns:
            List of (text, metadata) tuples. Metadata contains page_number or chapter.
        """
        pass
```

### src/domain/interfaces/embedding_service.py

```python
"""Embedding service interface."""

from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    """Interface for text embedding."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of strings to embed.

        Returns:
            List of embedding vectors.
        """
        pass

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a single query.

        Args:
            query: Query string.

        Returns:
            Embedding vector.
        """
        pass
```

### src/domain/interfaces/vector_store.py

```python
"""Vector store interface."""

from abc import ABC, abstractmethod

from ..entities import Chunk


class VectorStore(ABC):
    """Interface for vector storage and retrieval."""

    @abstractmethod
    async def add_chunks(self, chunks: list[Chunk], collection_id: str) -> None:
        """
        Add chunks to vector store.

        Args:
            chunks: Chunks with embeddings.
            collection_id: Collection/session identifier.
        """
        pass

    @abstractmethod
    async def search(
        self, query_embedding: list[float], collection_id: str, top_k: int = 5
    ) -> list[Chunk]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query vector.
            collection_id: Collection to search.
            top_k: Number of results.

        Returns:
            List of matching chunks, most relevant first.
        """
        pass

    @abstractmethod
    async def delete_collection(self, collection_id: str) -> None:
        """Delete a collection and all its chunks."""
        pass

    @abstractmethod
    async def collection_exists(self, collection_id: str) -> bool:
        """Check if collection exists."""
        pass
```

### src/domain/interfaces/llm_client.py

```python
"""LLM client interface."""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Interface for LLM interactions."""

    @abstractmethod
    async def generate(self, prompt: str, context: list[str]) -> str:
        """
        Generate response using context.

        Args:
            prompt: User question.
            context: Relevant text chunks for RAG.

        Returns:
            Generated response.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if LLM service is available."""
        pass
```

### src/domain/interfaces/__init__.py

```python
"""Domain interfaces."""

from .document_parser import DocumentParser
from .embedding_service import EmbeddingService
from .vector_store import VectorStore
from .llm_client import LLMClient

__all__ = ["DocumentParser", "EmbeddingService", "VectorStore", "LLMClient"]
```

### src/domain/exceptions.py (extended)

```python
"""Domain-level exceptions."""


class BookChatError(Exception):
    """Base exception for LocalBookChat application."""

    pass


class UnsupportedFileTypeError(BookChatError):
    """Raised when file type is not PDF or EPUB."""

    pass


class FileSizeLimitError(BookChatError):
    """Raised when file exceeds size limit."""

    pass


class BookNotFoundError(BookChatError):
    """Raised when book ID doesn't exist."""

    pass


class LLMConnectionError(BookChatError):
    """Raised when LLM service is unreachable."""

    pass


class SessionLimitError(BookChatError):
    """Raised when session book limit exceeded."""

    pass
```

## Verification

```bash
# Run domain tests
pytest tests/unit/domain/ -v

# Verify no external imports in domain
grep -r "^import " src/domain/ | grep -v "from \." | grep -v "dataclass\|abc\|uuid\|datetime\|pathlib\|typing"
# Should return nothing

# Lint
ruff check src/domain/
```

All tests must pass. Domain should have zero external dependencies.

## Commit

```bash
git add .
git commit -m "feat: implement domain entities and interfaces"
```

## Next Phase

Proceed to `docs/phases/PHASE_2_PARSING.md`
