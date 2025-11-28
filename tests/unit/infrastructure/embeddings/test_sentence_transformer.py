"""Tests for sentence transformer embeddings."""

import pytest

from src.infrastructure.embeddings import SentenceTransformerEmbedder


class TestSentenceTransformerEmbedder:
    @pytest.fixture
    def embedder(self) -> SentenceTransformerEmbedder:
        # Use small model for faster tests
        return SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")

    def test_embed_single_text(self, embedder: SentenceTransformerEmbedder):
        texts = ["This is a test sentence."]
        embeddings = embedder.embed(texts)

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 384  # MiniLM dimension

    def test_embed_multiple_texts(self, embedder: SentenceTransformerEmbedder):
        texts = ["First sentence.", "Second sentence.", "Third sentence."]
        embeddings = embedder.embed(texts)

        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)

    def test_embed_query(self, embedder: SentenceTransformerEmbedder):
        embedding = embedder.embed_query("What is the meaning of life?")

        assert len(embedding) == 384
        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)

    def test_similar_texts_have_similar_embeddings(self, embedder: SentenceTransformerEmbedder):
        # Cosine similarity helper
        def cosine_sim(a: list[float], b: list[float]) -> float:
            import math

            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            return dot / (norm_a * norm_b)

        similar_1 = embedder.embed_query("The cat sat on the mat.")
        similar_2 = embedder.embed_query("A cat is sitting on a rug.")
        different = embedder.embed_query("Python is a programming language.")

        sim_score = cosine_sim(similar_1, similar_2)
        diff_score = cosine_sim(similar_1, different)

        assert sim_score > diff_score  # Similar texts more similar

    def test_embed_empty_list(self, embedder: SentenceTransformerEmbedder):
        embeddings = embedder.embed([])
        assert embeddings == []
