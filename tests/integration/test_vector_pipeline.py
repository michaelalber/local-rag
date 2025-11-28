"""Integration tests for embedding + vector store pipeline."""

from pathlib import Path
from uuid import uuid4

import pytest

from src.domain.entities import Chunk
from src.infrastructure.embeddings import SentenceTransformerEmbedder
from src.infrastructure.vectorstore import ChromaVectorStore


class TestVectorPipeline:
    """Test the full embed -> store -> search pipeline."""

    @pytest.fixture
    def embedder(self) -> SentenceTransformerEmbedder:
        return SentenceTransformerEmbedder()

    @pytest.fixture
    def store(self, tmp_path: Path) -> ChromaVectorStore:
        return ChromaVectorStore(persist_dir=tmp_path / "chroma")

    @pytest.mark.asyncio
    async def test_semantic_search_finds_relevant_chunks(
        self, embedder: SentenceTransformerEmbedder, store: ChromaVectorStore
    ):
        """Test that semantic search returns relevant results."""
        book_id = uuid4()
        texts = [
            "Python is great for machine learning and data science.",
            "JavaScript is commonly used for web development.",
            "The cat sat on the warm windowsill.",
            "Deep learning models require significant GPU memory.",
        ]

        # Create chunks with real embeddings
        chunks = []
        embeddings = embedder.embed(texts)
        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            chunks.append(
                Chunk(
                    id=uuid4(),
                    book_id=book_id,
                    content=text,
                    page_number=i + 1,
                    embedding=emb,
                )
            )

        # Store chunks
        collection_id = "semantic-test"
        await store.add_chunks(chunks, collection_id)

        # Search for ML-related content
        query = "What programming language is good for AI?"
        query_embedding = embedder.embed_query(query)

        results = await store.search(
            query_embedding=query_embedding, collection_id=collection_id, top_k=2
        )

        # Should return Python and deep learning chunks, not cat chunk
        result_texts = [r.content for r in results]
        assert any("Python" in t or "learning" in t for t in result_texts)
        assert not any("cat" in t for t in result_texts)

    @pytest.mark.asyncio
    async def test_persistence_survives_reload(
        self, embedder: SentenceTransformerEmbedder, tmp_path: Path
    ):
        """Test that data persists across store instances."""
        persist_dir = tmp_path / "persist_test"
        collection_id = "persist-session"
        book_id = uuid4()

        # Create and populate store
        store1 = ChromaVectorStore(persist_dir=persist_dir)
        chunk = Chunk(
            id=uuid4(),
            book_id=book_id,
            content="Persistent data test content.",
            page_number=1,
            embedding=embedder.embed_query("Persistent data test content."),
        )
        await store1.add_chunks([chunk], collection_id)

        # Create new store instance pointing to same directory
        store2 = ChromaVectorStore(persist_dir=persist_dir)

        # Should find the data
        results = await store2.search(
            query_embedding=embedder.embed_query("persistent data"),
            collection_id=collection_id,
            top_k=1,
        )

        assert len(results) == 1
        assert "Persistent" in results[0].content
