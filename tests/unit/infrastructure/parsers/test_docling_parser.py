"""Tests for Docling parser."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestDoclingParser:
    """Tests for DoclingParser with mocked docling dependency."""

    def test_lazy_loading_no_crash_without_docling(self):
        """Parser should instantiate without docling installed."""
        # Import should not fail even without docling
        from src.parsers.docling_parser import DoclingParser

        parser = DoclingParser()
        assert parser._converter is None
        assert parser._chunker is None

    def test_raises_import_error_when_docling_not_installed(self, tmp_path: Path):
        """Parser should raise helpful error when docling not installed."""
        from src.parsers.docling_parser import DoclingParser

        parser = DoclingParser()
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        # Mock the import to fail
        with patch.dict("sys.modules", {"docling": None, "docling.document_converter": None}):
            with pytest.raises(ImportError) as exc_info:
                parser.parse(test_file)

            assert "localbookchat[enhanced]" in str(exc_info.value)

    def test_handles_missing_file(self, tmp_path: Path):
        """Parser should raise FileNotFoundError for missing files."""
        from src.parsers.docling_parser import DoclingParser

        parser = DoclingParser()
        missing_file = tmp_path / "nonexistent.pdf"

        with pytest.raises(FileNotFoundError):
            parser.parse(missing_file)

        with pytest.raises(FileNotFoundError):
            parser.extract_text(missing_file)


class TestDoclingParserWithMocks:
    """Tests for DoclingParser functionality with mocked docling."""

    @pytest.fixture
    def mock_docling(self):
        """Mock docling modules."""
        mock_converter_class = MagicMock()
        mock_chunker_class = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "docling": MagicMock(),
                "docling.document_converter": MagicMock(
                    DocumentConverter=mock_converter_class
                ),
                "docling.chunking": MagicMock(HybridChunker=mock_chunker_class),
            },
        ):
            yield {
                "converter_class": mock_converter_class,
                "chunker_class": mock_chunker_class,
            }

    @pytest.fixture
    def sample_pdf(self, tmp_path: Path) -> Path:
        """Create a sample PDF file."""
        pdf_file = tmp_path / "sample.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")
        return pdf_file

    def test_parse_extracts_title_from_filename(self, mock_docling, sample_pdf: Path):
        """Parse should extract title from document or filename."""
        # Setup mock
        mock_doc = MagicMock()
        mock_doc.name = None  # No document name
        mock_result = MagicMock()
        mock_result.document = mock_doc
        mock_docling["converter_class"].return_value.convert.return_value = mock_result

        from src.parsers.docling_parser import DoclingParser

        parser = DoclingParser()
        title, author = parser.parse(sample_pdf)

        assert title == "sample"  # Falls back to filename stem
        assert author is None

    def test_parse_extracts_title_from_document(self, mock_docling, sample_pdf: Path):
        """Parse should use document name when available."""
        # Setup mock with document name
        mock_doc = MagicMock()
        mock_doc.name = "My Document Title"
        mock_result = MagicMock()
        mock_result.document = mock_doc
        mock_docling["converter_class"].return_value.convert.return_value = mock_result

        from src.parsers.docling_parser import DoclingParser

        parser = DoclingParser()
        title, author = parser.parse(sample_pdf)

        assert title == "My Document Title"

    def test_extract_text_returns_segments_with_metadata(
        self, mock_docling, sample_pdf: Path
    ):
        """Extract text should return segments with page numbers and sections."""
        # Setup mock chunks
        mock_chunk1 = MagicMock()
        mock_chunk1.text = "First chunk content"
        mock_chunk1.meta = MagicMock()
        mock_chunk1.meta.page = 1
        mock_chunk1.meta.headings = ["Chapter 1", "Introduction"]

        mock_chunk2 = MagicMock()
        mock_chunk2.text = "Second chunk content"
        mock_chunk2.meta = MagicMock()
        mock_chunk2.meta.page = 2
        mock_chunk2.meta.headings = ["Chapter 1", "Details"]

        mock_doc = MagicMock()
        mock_result = MagicMock()
        mock_result.document = mock_doc

        mock_docling["converter_class"].return_value.convert.return_value = mock_result
        mock_docling["chunker_class"].return_value.chunk.return_value = [
            mock_chunk1,
            mock_chunk2,
        ]

        from src.parsers.docling_parser import DoclingParser

        parser = DoclingParser()
        segments = parser.extract_text(sample_pdf)

        assert len(segments) == 2

        text1, meta1 = segments[0]
        assert text1 == "First chunk content"
        assert meta1["page_number"] == 1
        assert meta1["section"] == "Introduction"
        assert meta1["section_hierarchy"] == ["Chapter 1", "Introduction"]

        text2, meta2 = segments[1]
        assert text2 == "Second chunk content"
        assert meta2["page_number"] == 2

    def test_extract_text_skips_empty_chunks(self, mock_docling, sample_pdf: Path):
        """Extract text should skip empty chunks."""
        mock_chunk1 = MagicMock()
        mock_chunk1.text = "Valid content"
        mock_chunk1.meta = None

        mock_chunk2 = MagicMock()
        mock_chunk2.text = "   "  # Empty after strip
        mock_chunk2.meta = None

        mock_doc = MagicMock()
        mock_result = MagicMock()
        mock_result.document = mock_doc

        mock_docling["converter_class"].return_value.convert.return_value = mock_result
        mock_docling["chunker_class"].return_value.chunk.return_value = [
            mock_chunk1,
            mock_chunk2,
        ]

        from src.parsers.docling_parser import DoclingParser

        parser = DoclingParser()
        segments = parser.extract_text(sample_pdf)

        assert len(segments) == 1
        assert segments[0][0] == "Valid content"

    def test_extract_text_handles_missing_metadata(self, mock_docling, sample_pdf: Path):
        """Extract text should handle chunks without metadata gracefully."""
        mock_chunk = MagicMock()
        mock_chunk.text = "Content without metadata"
        mock_chunk.meta = None

        mock_doc = MagicMock()
        mock_result = MagicMock()
        mock_result.document = mock_doc

        mock_docling["converter_class"].return_value.convert.return_value = mock_result
        mock_docling["chunker_class"].return_value.chunk.return_value = [mock_chunk]

        from src.parsers.docling_parser import DoclingParser

        parser = DoclingParser()
        segments = parser.extract_text(sample_pdf)

        assert len(segments) == 1
        text, metadata = segments[0]
        assert text == "Content without metadata"
        assert metadata == {}  # Empty metadata when not available


class TestParserFactory:
    """Tests for parser factory with docling integration."""

    def test_factory_returns_pdf_parser_by_default(self, tmp_path: Path):
        """Factory should return PdfParser when docling not enabled."""
        import os

        # Ensure docling is disabled
        os.environ.pop("USE_DOCLING_PARSER", None)

        from src.parsers import PdfParser, get_parser

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        parser = get_parser(pdf_file)
        assert isinstance(parser, PdfParser)

    def test_factory_raises_for_docling_extensions_when_disabled(self, tmp_path: Path):
        """Factory should raise for docling-only extensions when disabled."""
        import os

        os.environ.pop("USE_DOCLING_PARSER", None)

        from src.models import UnsupportedFileTypeError
        from src.parsers import get_parser

        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"PK")

        with pytest.raises(UnsupportedFileTypeError) as exc_info:
            get_parser(docx_file)

        assert "USE_DOCLING_PARSER=true" in str(exc_info.value)
        assert "localbookchat[enhanced]" in str(exc_info.value)

    def test_factory_returns_docling_parser_when_enabled(self, tmp_path: Path):
        """Factory should return DoclingParser when enabled."""
        import os

        os.environ["USE_DOCLING_PARSER"] = "true"

        try:
            from src.parsers import get_parser
            from src.parsers.docling_parser import DoclingParser

            pdf_file = tmp_path / "test.pdf"
            pdf_file.write_bytes(b"%PDF-1.4")

            parser = get_parser(pdf_file)
            assert isinstance(parser, DoclingParser)
        finally:
            os.environ.pop("USE_DOCLING_PARSER", None)

    def test_factory_handles_docling_extensions_when_enabled(self, tmp_path: Path):
        """Factory should handle docling extensions when enabled."""
        import os

        os.environ["USE_DOCLING_PARSER"] = "true"

        try:
            from src.parsers import get_parser
            from src.parsers.docling_parser import DoclingParser

            docx_file = tmp_path / "test.docx"
            docx_file.write_bytes(b"PK")

            parser = get_parser(docx_file)
            assert isinstance(parser, DoclingParser)
        finally:
            os.environ.pop("USE_DOCLING_PARSER", None)
