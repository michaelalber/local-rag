"""Tests for domain entities."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from src.models import Book, Chunk, QueryRequest, QueryResponse


class TestBook:
    def test_create_book_with_valid_pdf(self):
        book = Book(
            id=uuid4(),
            title="Test Book",
            author="Test Author",
            file_path=Path("/uploads/test.pdf"),
            file_type="pdf",
            created_at=datetime.now(timezone.utc),
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
            created_at=datetime.now(timezone.utc),
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
                created_at=datetime.now(timezone.utc),
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
