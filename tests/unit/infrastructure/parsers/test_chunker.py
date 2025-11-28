"""Tests for text chunking."""

import pytest

from src.infrastructure.parsers.chunker import TextChunker


class TestTextChunker:
    @pytest.fixture
    def chunker(self) -> TextChunker:
        return TextChunker(chunk_size=100, overlap=20)

    def test_chunks_text_into_pieces(self, chunker: TextChunker):
        text = "word " * 100  # 500 chars
        chunks = chunker.chunk(text, metadata={"page": 1})
        assert len(chunks) > 1

    def test_chunks_include_metadata(self, chunker: TextChunker):
        text = "This is sample text for chunking."
        chunks = chunker.chunk(text, metadata={"page": 42, "chapter": "Intro"})
        assert all(c["metadata"]["page"] == 42 for c in chunks)

    def test_small_text_single_chunk(self, chunker: TextChunker):
        text = "Short text."
        chunks = chunker.chunk(text, metadata={})
        assert len(chunks) == 1

    def test_empty_text_returns_empty(self, chunker: TextChunker):
        chunks = chunker.chunk("", metadata={})
        assert chunks == []

    def test_overlap_creates_continuity(self):
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "A" * 30 + "B" * 30 + "C" * 30  # 90 chars
        chunks = chunker.chunk(text, metadata={})

        # With overlap, adjacent chunks should share some content
        if len(chunks) > 1:
            # Last chars of chunk 0 should appear in start of chunk 1
            assert chunks[0]["text"][-10:] in chunks[1]["text"] or len(chunks[0]["text"]) < 50
