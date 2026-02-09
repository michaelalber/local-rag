"""ChromaDB vector store implementation."""

import logging
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import chromadb
from chromadb.config import Settings

from src.models import Chunk

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """Vector store using ChromaDB with persistence."""

    def __init__(self, persist_dir: Path):
        """
        Args:
            persist_dir: Directory for ChromaDB persistence.
        """
        persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )

    async def add_chunks(self, chunks: list[Chunk], collection_id: str) -> None:
        """Add chunks with embeddings to collection."""
        if not chunks:
            return

        collection = self.client.get_or_create_collection(
            name=self._sanitize_collection_name(collection_id),
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )

        # Prepare data for ChromaDB
        ids = [str(c.id) for c in chunks]
        embeddings: list[list[float]] = [c.embedding for c in chunks if c.embedding]
        documents = [c.content for c in chunks]
        metadatas: list[dict[str, str | int | float | bool]] = [
            {
                "book_id": str(c.book_id),
                "page_number": c.page_number or -1,
                "chapter": c.chapter or "",
                "has_code": c.has_code,
                "code_language": c.code_language or "",
                "sequence_number": c.sequence_number,
                "parent_chunk_id": str(c.parent_chunk_id) if c.parent_chunk_id else "",
                "parent_content": c.parent_content or "",
            }
            for c in chunks
        ]

        if not embeddings or len(embeddings) != len(chunks):
            raise ValueError("All chunks must have embeddings")

        # ChromaDB has a max batch size (~5461), so batch large uploads
        batch_size = 1000
        total_chunks = len(chunks)

        for i in range(0, total_chunks, batch_size):
            end_idx = min(i + batch_size, total_chunks)
            batch_ids = ids[i:end_idx]
            batch_embeddings = embeddings[i:end_idx]
            batch_documents = documents[i:end_idx]
            batch_metadatas = metadatas[i:end_idx]

            collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,  # type: ignore[arg-type]
                documents=batch_documents,
                metadatas=batch_metadatas,  # type: ignore[arg-type]
            )

            if total_chunks > batch_size:
                logger.info(
                    "Added batch %d/%d (%d/%d chunks)",
                    i // batch_size + 1,
                    (total_chunks + batch_size - 1) // batch_size,
                    end_idx,
                    total_chunks,
                )

    async def get_collection_size(self, collection_id: str) -> int:
        """Get total number of chunks in collection."""
        collection_name = self._sanitize_collection_name(collection_id)

        existing = [c.name for c in self.client.list_collections()]
        if collection_name not in existing:
            return 0

        collection = self.client.get_collection(collection_name)
        return collection.count()

    async def search(
        self, query_embedding: list[float], collection_id: str, top_k: int = 5
    ) -> list[Chunk]:
        """Search for similar chunks."""
        collection_name = self._sanitize_collection_name(collection_id)

        # Check if collection exists
        existing = [c.name for c in self.client.list_collections()]
        if collection_name not in existing:
            return []

        collection = self.client.get_collection(collection_name)

        results = collection.query(
            query_embeddings=[query_embedding],  # type: ignore[arg-type]
            n_results=top_k,
            include=cast(Any, ["documents", "metadatas", "embeddings"]),
        )

        # Convert results to Chunk entities
        chunks = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = dict(results["metadatas"][0][i] if results["metadatas"] else {})

                page_num = metadata.get("page_number", -1)
                chunk = Chunk(
                    id=UUID(chunk_id),
                    book_id=UUID(
                        str(metadata.get("book_id", "00000000-0000-0000-0000-000000000000"))
                    ),
                    content=results["documents"][0][i] if results["documents"] else "",
                    page_number=int(page_num) if page_num != -1 else None,
                    chapter=str(metadata.get("chapter")) or None,
                    embedding=list(results["embeddings"][0][i])
                    if results.get("embeddings") and results["embeddings"]
                    else None,
                    has_code=bool(metadata.get("has_code", False)),
                    code_language=str(metadata.get("code_language")) or None,
                    sequence_number=int(metadata.get("sequence_number", 0)),
                    parent_chunk_id=(
                        UUID(str(metadata["parent_chunk_id"]))
                        if metadata.get("parent_chunk_id")
                        else None
                    ),
                    parent_content=str(metadata.get("parent_content")) or None,
                )
                chunks.append(chunk)

        return chunks

    async def delete_collection(self, collection_id: str) -> None:
        """Delete a collection."""
        collection_name = self._sanitize_collection_name(collection_id)
        try:
            self.client.delete_collection(collection_name)
        except ValueError:
            # ChromaDB raises ValueError when collection doesn't exist
            logger.debug("Collection %s doesn't exist, nothing to delete", collection_name)

    async def delete_book_chunks(self, collection_id: str, book_id: UUID) -> None:
        """Delete all chunks belonging to a specific book."""
        collection_name = self._sanitize_collection_name(collection_id)

        # Check if collection exists
        existing = [c.name for c in self.client.list_collections()]
        if collection_name not in existing:
            return  # Collection doesn't exist, nothing to delete

        collection = self.client.get_collection(collection_name)

        # Delete all chunks with matching book_id
        book_id_str = str(book_id)
        try:
            count_before = collection.count()
            collection.delete(where={"book_id": book_id_str})
            count_after = collection.count()
            deleted_count = count_before - count_after

            if deleted_count > 0:
                logger.info("Deleted %d chunks for book %s", deleted_count, book_id_str)
            else:
                logger.debug("No chunks found to delete for book %s", book_id_str)

        except chromadb.errors.ChromaError as e:
            logger.error("ChromaDB error deleting chunks for book %s: %s", book_id_str, e)
            raise

    async def collection_exists(self, collection_id: str) -> bool:
        """Check if collection exists."""
        collection_name = self._sanitize_collection_name(collection_id)
        existing = [c.name for c in self.client.list_collections()]
        return collection_name in existing

    async def get_neighbor_chunks(
        self, chunks: list[Chunk], collection_id: str, window: int = 1
    ) -> list[Chunk]:
        """Get neighboring chunks for contextual retrieval."""
        if not chunks or window < 1:
            return chunks

        collection_name = self._sanitize_collection_name(collection_id)

        # Check if collection exists
        existing = [c.name for c in self.client.list_collections()]
        if collection_name not in existing:
            return chunks

        collection = self.client.get_collection(collection_name)

        # Build set of sequence numbers to fetch for each book
        chunks_to_fetch: dict[str, set[int]] = {}  # book_id -> set of sequence numbers

        for chunk in chunks:
            book_id_str = str(chunk.book_id)
            if book_id_str not in chunks_to_fetch:
                chunks_to_fetch[book_id_str] = set()

            # Add the chunk itself and its neighbors
            seq = chunk.sequence_number
            for offset in range(-window, window + 1):
                target_seq = seq + offset
                if target_seq >= 0:  # Don't fetch negative sequence numbers
                    chunks_to_fetch[book_id_str].add(target_seq)

        # Fetch all chunks from ChromaDB
        all_chunks = []
        for book_id_str, seq_numbers in chunks_to_fetch.items():
            # ChromaDB doesn't support complex queries, so we need to fetch
            # all chunks for this book and filter in memory
            try:
                results = collection.get(
                    where={"book_id": book_id_str},
                    include=cast(Any, ["documents", "metadatas", "embeddings"]),
                )

                if results["ids"]:
                    for i, chunk_id in enumerate(results["ids"]):
                        metadata = dict(results["metadatas"][i] if results["metadatas"] else {})
                        chunk_seq = int(metadata.get("sequence_number", 0))

                        # Only include chunks in our target sequence range
                        if chunk_seq in seq_numbers:
                            # Check for embeddings safely
                            embedding: list[float] | None = None
                            raw_embeddings = results.get("embeddings")
                            if raw_embeddings is not None and i < len(raw_embeddings):
                                embedding = list(raw_embeddings[i])

                            page_num = metadata.get("page_number", -1)
                            chunk = Chunk(
                                id=UUID(chunk_id),
                                book_id=UUID(book_id_str),
                                content=results["documents"][i] if results["documents"] else "",
                                page_number=int(page_num) if page_num != -1 else None,
                                chapter=str(metadata.get("chapter")) or None,
                                embedding=embedding,
                                has_code=bool(metadata.get("has_code", False)),
                                code_language=str(metadata.get("code_language")) or None,
                                sequence_number=chunk_seq,
                                parent_chunk_id=UUID(str(metadata["parent_chunk_id"]))
                                if metadata.get("parent_chunk_id")
                                else None,
                                parent_content=str(metadata.get("parent_content")) or None,
                            )
                            all_chunks.append(chunk)

            except chromadb.errors.ChromaError as e:
                logger.warning("Error fetching neighbors for book %s: %s", book_id_str, e)
                continue

        # Deduplicate by chunk ID and sort by book_id, sequence_number
        unique_chunks = {chunk.id: chunk for chunk in all_chunks}
        sorted_chunks = sorted(
            unique_chunks.values(), key=lambda c: (str(c.book_id), c.sequence_number)
        )

        return sorted_chunks

    def _sanitize_collection_name(self, name: str) -> str:
        """
        Sanitize collection name for ChromaDB.

        ChromaDB requires: 3-63 chars, alphanumeric + underscores/hyphens,
        must start/end with alphanumeric.
        """
        # Replace invalid chars
        sanitized = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)

        # Ensure starts with letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = "c_" + sanitized

        # Ensure valid length
        sanitized = sanitized[:63]
        if len(sanitized) < 3:
            sanitized = sanitized + "_col"

        # Ensure ends with alphanumeric
        sanitized = sanitized.rstrip("-_") or "collection"

        return sanitized
