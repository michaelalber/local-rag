"""Tests for ChromaDB vector store."""

from pathlib import Path
from uuid import uuid4

import pytest

from src.domain.entities import Chunk
from src.infrastructure.vectorstore import ChromaVectorStore


class TestChromaVectorStore:
    @pytest.fixture
    def store(self, tmp_path: Path) -> ChromaVectorStore:
        return ChromaVectorStore(persist_dir=tmp_path / "chroma")

    @pytest.fixture
    def sample_chunks(self) -> list[Chunk]:
        book_id = uuid4()
        return [
            Chunk(
                id=uuid4(),
                book_id=book_id,
                content="Python is a programming language.",
                page_number=1,
                embedding=[0.1] * 384,  # Dummy embedding
            ),
            Chunk(
                id=uuid4(),
                book_id=book_id,
                content="Machine learning uses algorithms.",
                page_number=2,
                embedding=[0.2] * 384,
            ),
            Chunk(
                id=uuid4(),
                book_id=book_id,
                content="Cats are furry animals.",
                page_number=3,
                embedding=[0.9] * 384,  # Different
            ),
        ]

    @pytest.mark.asyncio
    async def test_add_and_search_chunks(
        self, store: ChromaVectorStore, sample_chunks: list[Chunk]
    ):
        collection_id = "test-session"

        # Add chunks
        await store.add_chunks(sample_chunks, collection_id)

        # Search with embedding similar to first chunk
        results = await store.search(
            query_embedding=[0.1] * 384, collection_id=collection_id, top_k=2
        )

        assert len(results) <= 2
        assert all(isinstance(c, Chunk) for c in results)

    @pytest.mark.asyncio
    async def test_collection_exists(
        self, store: ChromaVectorStore, sample_chunks: list[Chunk]
    ):
        collection_id = "existence-test"

        assert not await store.collection_exists(collection_id)

        await store.add_chunks(sample_chunks, collection_id)

        assert await store.collection_exists(collection_id)

    @pytest.mark.asyncio
    async def test_delete_collection(
        self, store: ChromaVectorStore, sample_chunks: list[Chunk]
    ):
        collection_id = "delete-test"

        await store.add_chunks(sample_chunks, collection_id)
        assert await store.collection_exists(collection_id)

        await store.delete_collection(collection_id)
        assert not await store.collection_exists(collection_id)

    @pytest.mark.asyncio
    async def test_search_empty_collection(self, store: ChromaVectorStore):
        # Search non-existent collection should return empty
        results = await store.search(
            query_embedding=[0.1] * 384, collection_id="nonexistent", top_k=5
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_search_returns_metadata(
        self, store: ChromaVectorStore, sample_chunks: list[Chunk]
    ):
        collection_id = "metadata-test"
        await store.add_chunks(sample_chunks, collection_id)

        results = await store.search(
            query_embedding=[0.1] * 384, collection_id=collection_id, top_k=1
        )

        assert len(results) == 1
        # Should have page_number from original chunk
        assert results[0].page_number is not None
