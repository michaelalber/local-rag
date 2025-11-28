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
