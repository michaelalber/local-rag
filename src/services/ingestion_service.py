"""Book ingestion service."""

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.models import Book, Chunk, DocumentParsingError
from src.parsers import DocumentParser, FileValidator, TextChunker
from src.vectorstore import ChromaVectorStore


class BookIngestionService:
    """Orchestrates book ingestion: parse, chunk, embed, store."""

    def __init__(
        self,
        parser_factory: Callable[[Path], DocumentParser],
        chunker: TextChunker,
        embedder,  # OllamaEmbedder or SentenceTransformerEmbedder
        vector_store: ChromaVectorStore,
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

    async def ingest_book(
        self, file_path: Path, session_id: str, original_filename: str | None = None
    ) -> Book:
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
        try:
            title, author = parser.parse(file_path)
            text_segments = parser.extract_text(file_path)
        except Exception as e:
            raise DocumentParsingError(
                f"Failed to parse document: {e}"
            ) from e

        # Use original filename as title fallback if title looks like a temp file
        if original_filename and (not title or title.startswith("tmp") or len(title) < 3):
            title = Path(original_filename).stem

        # Chunk all segments with hierarchical chunking
        all_chunks_data = []
        for text, metadata in text_segments:
            chunk_dicts = self.chunker.chunk_hierarchical(text, metadata)
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

        # Create Chunk entities with hierarchical fields
        chunks = []
        for chunk_data, embedding in zip(all_chunks_data, embeddings):
            metadata = chunk_data["metadata"]
            chunk = Chunk(
                id=uuid4(),
                book_id=book_id,
                content=chunk_data["text"],
                page_number=metadata.get("page_number"),
                chapter=metadata.get("chapter"),
                embedding=embedding,
                has_code=metadata.get("has_code", False),
                code_language=metadata.get("code_language"),
                sequence_number=metadata.get("sequence_number", 0),
                parent_chunk_id=metadata.get("parent_chunk_id"),
                parent_content=metadata.get("parent_content"),
            )
            chunks.append(chunk)

        # Store in vector database
        await self.vector_store.add_chunks(chunks, session_id)

        return book
