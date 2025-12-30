"""Sentence transformer embedding service."""

from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbedder:
    """Embedding service using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Args:
            model_name: HuggingFace model name. Default is fast and good quality.
        """
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()

    @property
    def dimension(self) -> int:
        """Embedding dimension for this model."""
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        # convert_to_numpy for efficiency, then to list for JSON compatibility
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single query."""
        embedding = self.model.encode(query, convert_to_numpy=True)
        return embedding.tolist()
