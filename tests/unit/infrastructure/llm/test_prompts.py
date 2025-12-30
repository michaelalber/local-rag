"""Unit tests for RAG prompt builder."""

from uuid import uuid4

import pytest

from src.models import Chunk
from src.llm import RAGPromptBuilder


class TestRAGPromptBuilder:
    """Test the RAG prompt construction."""

    @pytest.fixture
    def builder(self) -> RAGPromptBuilder:
        return RAGPromptBuilder()

    @pytest.fixture
    def sample_chunks(self) -> list[Chunk]:
        """Sample chunks for testing."""
        book_id = uuid4()
        return [
            Chunk(
                id=uuid4(),
                book_id=book_id,
                content="Python is a high-level programming language.",
                page_number=1,
                chapter="Introduction",
            ),
            Chunk(
                id=uuid4(),
                book_id=book_id,
                content="It supports multiple programming paradigms.",
                page_number=2,
                chapter="Introduction",
            ),
            Chunk(
                id=uuid4(),
                book_id=book_id,
                content="Python has a large standard library.",
                page_number=5,
                chapter="Features",
            ),
        ]

    def test_build_prompt_with_context(
        self, builder: RAGPromptBuilder, sample_chunks: list[Chunk]
    ):
        """Test prompt generation with context chunks."""
        query = "What is Python?"
        prompt = builder.build_prompt(query=query, context_chunks=sample_chunks)

        # Should include the query
        assert "What is Python?" in prompt

        # Should include context from all chunks
        assert "Python is a high-level programming language" in prompt
        assert "multiple programming paradigms" in prompt
        assert "large standard library" in prompt

        # Should have clear structure
        assert "context" in prompt.lower() or "based on" in prompt.lower()

    def test_build_prompt_without_context(self, builder: RAGPromptBuilder):
        """Test prompt when no context is available."""
        query = "What is Python?"
        prompt = builder.build_prompt(query=query, context_chunks=[])

        # Should still include the query
        assert "What is Python?" in prompt

        # Should indicate no context available
        assert (
            "no relevant" in prompt.lower()
            or "cannot find" in prompt.lower()
            or "no context" in prompt.lower()
        )

    def test_build_prompt_includes_source_metadata(
        self, builder: RAGPromptBuilder, sample_chunks: list[Chunk]
    ):
        """Test that source attribution metadata is included."""
        query = "Tell me about Python"
        prompt = builder.build_prompt(query=query, context_chunks=sample_chunks)

        # Should include page numbers or chapter references
        assert "page" in prompt.lower() or "chapter" in prompt.lower()

    def test_build_prompt_limits_context_chunks(self, sample_chunks: list[Chunk]):
        """Test that very long context is handled appropriately."""
        # Use a builder with stricter limit for this test
        limited_builder = RAGPromptBuilder(max_context_length=20000)

        # Create many chunks
        book_id = uuid4()
        many_chunks = [
            Chunk(
                id=uuid4(),
                book_id=book_id,
                content=f"Content chunk number {i} " * 100,
                page_number=i,
            )
            for i in range(20)
        ]

        query = "What is this about?"
        prompt = limited_builder.build_prompt(query=query, context_chunks=many_chunks)

        # Prompt should be constructed successfully
        assert query in prompt
        assert len(prompt) > 0

        # Should not be excessively long (reasonable token limit)
        # Assuming ~4 chars per token, keep under ~8000 tokens
        assert len(prompt) < 32000

    def test_build_prompt_handles_chunks_without_metadata(
        self, builder: RAGPromptBuilder
    ):
        """Test handling chunks with minimal metadata."""
        chunks = [
            Chunk(
                id=uuid4(),
                book_id=uuid4(),
                content="Some content without page or chapter.",
            )
        ]

        query = "What is this?"
        prompt = builder.build_prompt(query=query, context_chunks=chunks)

        assert query in prompt
        assert "Some content without page or chapter" in prompt

    def test_build_prompt_formats_consistently(
        self, builder: RAGPromptBuilder, sample_chunks: list[Chunk]
    ):
        """Test that prompt format is consistent across calls."""
        query = "What is Python?"

        prompt1 = builder.build_prompt(query=query, context_chunks=sample_chunks)
        prompt2 = builder.build_prompt(query=query, context_chunks=sample_chunks)

        # Same input should produce same output
        assert prompt1 == prompt2

    def test_build_prompt_instructs_llm_appropriately(
        self, builder: RAGPromptBuilder, sample_chunks: list[Chunk]
    ):
        """Test that prompt gives clear instructions to LLM."""
        query = "Explain Python features"
        prompt = builder.build_prompt(query=query, context_chunks=sample_chunks)

        # Should contain instruction keywords
        instruction_keywords = ["answer", "based on", "context", "use", "provided"]
        assert any(keyword in prompt.lower() for keyword in instruction_keywords)

        # Should encourage citation or source reference
        citation_keywords = ["source", "reference", "according to", "cite"]
        assert any(keyword in prompt.lower() for keyword in citation_keywords)
