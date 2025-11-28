# Phase 3: Embedding & Vector Store

## Objective

Implement sentence-transformers embedding service and ChromaDB vector store.

## Files to Create

```
src/infrastructure/
├── embeddings/
│   ├── __init__.py
│   └── sentence_transformer.py
└── vectorstore/
    ├── __init__.py
    └── chroma_store.py
tests/
├── unit/infrastructure/
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── test_sentence_transformer.py
│   └── vectorstore/
│       ├── __init__.py
│       └── test_chroma_store.py
└── integration/
    └── test_vector_pipeline.py
```

## Write Tests First

### tests/unit/infrastructure/embeddings/test_sentence_transformer.py

```python
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
```

### tests/unit/infrastructure/vectorstore/test_chroma_store.py

```python
"""Tests for ChromaDB vector store."""

import pytest
from uuid import uuid4
from pathlib import Path

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
            query_embedding=[0.1] * 384,
            collection_id=collection_id,
            top_k=2
        )
        
        assert len(results) <= 2
        assert all(isinstance(c, Chunk) for c in results)

    @pytest.mark.asyncio
    async def test_collection_exists(self, store: ChromaVectorStore, sample_chunks: list[Chunk]):
        collection_id = "existence-test"
        
        assert not await store.collection_exists(collection_id)
        
        await store.add_chunks(sample_chunks, collection_id)
        
        assert await store.collection_exists(collection_id)

    @pytest.mark.asyncio
    async def test_delete_collection(self, store: ChromaVectorStore, sample_chunks: list[Chunk]):
        collection_id = "delete-test"
        
        await store.add_chunks(sample_chunks, collection_id)
        assert await store.collection_exists(collection_id)
        
        await store.delete_collection(collection_id)
        assert not await store.collection_exists(collection_id)

    @pytest.mark.asyncio
    async def test_search_empty_collection(self, store: ChromaVectorStore):
        # Search non-existent collection should return empty
        results = await store.search(
            query_embedding=[0.1] * 384,
            collection_id="nonexistent",
            top_k=5
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_search_returns_metadata(
        self, store: ChromaVectorStore, sample_chunks: list[Chunk]
    ):
        collection_id = "metadata-test"
        await store.add_chunks(sample_chunks, collection_id)
        
        results = await store.search(
            query_embedding=[0.1] * 384,
            collection_id=collection_id,
            top_k=1
        )
        
        assert len(results) == 1
        # Should have page_number from original chunk
        assert results[0].page_number is not None
```

### tests/integration/test_vector_pipeline.py

```python
"""Integration tests for embedding + vector store pipeline."""

import pytest
from uuid import uuid4
from pathlib import Path

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
            chunks.append(Chunk(
                id=uuid4(),
                book_id=book_id,
                content=text,
                page_number=i + 1,
                embedding=emb,
            ))
        
        # Store chunks
        collection_id = "semantic-test"
        await store.add_chunks(chunks, collection_id)
        
        # Search for ML-related content
        query = "What programming language is good for AI?"
        query_embedding = embedder.embed_query(query)
        
        results = await store.search(
            query_embedding=query_embedding,
            collection_id=collection_id,
            top_k=2
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
            top_k=1
        )
        
        assert len(results) == 1
        assert "Persistent" in results[0].content
```

## Implementation

### src/infrastructure/embeddings/sentence_transformer.py

```python
"""Sentence transformer embedding service."""

from sentence_transformers import SentenceTransformer

from src.domain.interfaces import EmbeddingService


class SentenceTransformerEmbedder(EmbeddingService):
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
```

### src/infrastructure/embeddings/__init__.py

```python
"""Embedding infrastructure."""

from .sentence_transformer import SentenceTransformerEmbedder

__all__ = ["SentenceTransformerEmbedder"]
```

### src/infrastructure/vectorstore/chroma_store.py

```python
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
                    book_id=UUID(metadata.get("book_id", "00000000-0000-0000-0000-000000000000")),
                    content=results["documents"][0][i] if results["documents"] else "",
                    page_number=metadata.get("page_number") if metadata.get("page_number", -1) != -1 else None,
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
```

### src/infrastructure/vectorstore/__init__.py

```python
"""Vector store infrastructure."""

from .chroma_store import ChromaVectorStore

__all__ = ["ChromaVectorStore"]
```

## Verification

```bash
# Run embedding tests
pytest tests/unit/infrastructure/embeddings/ -v

# Run vector store tests
pytest tests/unit/infrastructure/vectorstore/ -v

# Run integration tests (may be slower due to model loading)
pytest tests/integration/ -v

# Quick manual test
python -c "
from src.infrastructure.embeddings import SentenceTransformerEmbedder
from src.infrastructure.vectorstore import ChromaVectorStore
from src.domain.entities import Chunk
from pathlib import Path
from uuid import uuid4
import asyncio

async def test():
    embedder = SentenceTransformerEmbedder()
    store = ChromaVectorStore(Path('./data/chroma_test'))
    
    # Create test chunk
    text = 'The quick brown fox jumps over the lazy dog.'
    embedding = embedder.embed_query(text)
    chunk = Chunk(id=uuid4(), book_id=uuid4(), content=text, page_number=1, embedding=embedding)
    
    await store.add_chunks([chunk], 'test-session')
    
    # Search
    results = await store.search(embedder.embed_query('fox jumping'), 'test-session', top_k=1)
    print(f'Found: {results[0].content}')
    
    # Cleanup
    await store.delete_collection('test-session')

asyncio.run(test())
"
```

## Commit

```bash
git add .
git commit -m "feat: implement embedding service and ChromaDB vector store"
```

## Next Phase

Proceed to `docs/phases/PHASE_4_LLM.md`
