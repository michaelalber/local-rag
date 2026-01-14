"""Ollama embedding service."""

import httpx

# Known dimensions for common Ollama embedding models
OLLAMA_EMBED_DIMENSIONS = {
    "nomic-embed-text": 768,
    "nomic-embed-text:latest": 768,
    "mxbai-embed-large": 1024,
    "mxbai-embed-large:latest": 1024,
    "all-minilm": 384,
    "all-minilm:latest": 384,
}


class OllamaEmbedder:
    """Embedding service using Ollama API."""

    def __init__(
        self,
        model_name: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
    ):
        """
        Args:
            model_name: Ollama embedding model name.
            base_url: Ollama API base URL.
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self._dimension = OLLAMA_EMBED_DIMENSIONS.get(model_name, 768)

    @property
    def dimension(self) -> int:
        """Embedding dimension for this model."""
        return self._dimension

    def _embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        # Longer timeout to handle model loading on first request
        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        # Ollama doesn't support batch embedding, so we process sequentially
        embeddings = []
        for text in texts:
            embedding = self._embed_single(text)
            embeddings.append(embedding)

        return embeddings

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single query."""
        return self._embed_single(query)
