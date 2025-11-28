"""ChromaDB vector store implementation."""

from pathlib import Path
from uuid import UUID

import chromadb
from chromadb.config import Settings

from src.domain.entities import Chunk
from src.domain.interfaces import VectorStore


class ChromaVectorStore(VectorStore):
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
        embeddings = [c.embedding for c in chunks if c.embedding]
        documents = [c.content for c in chunks]
        metadatas = [
            {
                "book_id": str(c.book_id),
                "page_number": c.page_number or -1,
                "chapter": c.chapter or "",
            }
            for c in chunks
        ]

        if not embeddings or len(embeddings) != len(chunks):
            raise ValueError("All chunks must have embeddings")

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

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
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "embeddings"],
        )

        # Convert results to Chunk entities
        chunks = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}

                chunk = Chunk(
                    id=UUID(chunk_id),
                    book_id=UUID(
                        metadata.get("book_id", "00000000-0000-0000-0000-000000000000")
                    ),
                    content=results["documents"][0][i] if results["documents"] else "",
                    page_number=metadata.get("page_number")
                    if metadata.get("page_number", -1) != -1
                    else None,
                    chapter=metadata.get("chapter") or None,
                    embedding=results["embeddings"][0][i] if results.get("embeddings") else None,
                )
                chunks.append(chunk)

        return chunks

    async def delete_collection(self, collection_id: str) -> None:
        """Delete a collection."""
        collection_name = self._sanitize_collection_name(collection_id)
        try:
            self.client.delete_collection(collection_name)
        except ValueError:
            pass  # Collection doesn't exist, that's fine

    async def collection_exists(self, collection_id: str) -> bool:
        """Check if collection exists."""
        collection_name = self._sanitize_collection_name(collection_id)
        existing = [c.name for c in self.client.list_collections()]
        return collection_name in existing

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
