"""Vector store interface."""

from abc import ABC, abstractmethod
from uuid import UUID

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
    async def delete_book_chunks(self, collection_id: str, book_id: UUID) -> None:
        """
        Delete all chunks belonging to a specific book.

        Args:
            collection_id: Collection/session identifier.
            book_id: Book identifier to delete chunks for.
        """
        pass

    @abstractmethod
    async def collection_exists(self, collection_id: str) -> bool:
        """Check if collection exists."""
        pass
