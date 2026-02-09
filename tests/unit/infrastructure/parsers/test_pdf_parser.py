"""Tests for PDF parsing."""

from pathlib import Path

import pytest
from src.parsers import PdfParser


class TestPdfParser:
    @pytest.fixture
    def parser(self) -> PdfParser:
        return PdfParser()

    @pytest.fixture
    def sample_pdf(self, sample_data_dir: Path) -> Path:
        return sample_data_dir / "sample.pdf"

    def test_extracts_text_from_pdf(self, parser: PdfParser, sample_pdf: Path):
        if not sample_pdf.exists():
            pytest.skip("Sample PDF not available")

        pages = parser.extract_text(sample_pdf)
        assert len(pages) > 0
        assert all(isinstance(text, str) for text, _ in pages)

    def test_extracts_page_numbers(self, parser: PdfParser, sample_pdf: Path):
        if not sample_pdf.exists():
            pytest.skip("Sample PDF not available")

        pages = parser.extract_text(sample_pdf)
        for _text, metadata in pages:
            assert "page_number" in metadata
            assert isinstance(metadata["page_number"], int)

    def test_handles_missing_file(self, parser: PdfParser):
        with pytest.raises(FileNotFoundError):
            parser.extract_text(Path("/nonexistent/file.pdf"))
