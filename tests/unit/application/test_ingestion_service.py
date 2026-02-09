"""Tests for book ingestion service."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from src.models import Book, Chunk
from src.services import BookIngestionService


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
        chunker.chunk_hierarchical.return_value = [
            {"text": "Chunk 1", "metadata": {"page_number": 1}},
            {"text": "Chunk 2", "metadata": {"page_number": 1}},
        ]
        return chunker

    @pytest.fixture
    def mock_embedder(self):
        embedder = Mock()
        embedder.embed.side_effect = lambda texts: [[0.1] * 384 for _ in texts]
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
        mock_chunker.chunk_hierarchical.return_value = [
            {"text": "C1", "metadata": {}},
            {"text": "C2", "metadata": {}},
        ]

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"content")

        book = await service.ingest_book(file_path=test_file, session_id="s1")

        # 2 pages x 2 chunks each
        assert book.chunk_count == 4
