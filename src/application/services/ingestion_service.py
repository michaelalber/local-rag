"""Book ingestion service."""

from datetime import datetime, timezone
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
            created_at=datetime.now(timezone.utc),
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
                has_code=chunk_data["metadata"].get("has_code", False),
                code_language=chunk_data["metadata"].get("code_language"),
            )
            chunks.append(chunk)

        # Store in vector database
        await self.vector_store.add_chunks(chunks, session_id)

        return book
