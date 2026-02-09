"""Tests for plain text parsing."""

from pathlib import Path

import pytest
from src.parsers import TextParser


class TestTextParser:
    @pytest.fixture
    def parser(self) -> TextParser:
        return TextParser()

    def test_parse_returns_title_from_filename(self, parser: TextParser, tmp_path: Path):
        test_file = tmp_path / "my_document.txt"
        test_file.write_text("Some content here.")

        title, author = parser.parse(test_file)

        assert title == "my_document"
        assert author is None

    def test_extract_text_returns_content(self, parser: TextParser, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!\nThis is a test.")

        result = parser.extract_text(test_file)

        assert len(result) == 1
        text, metadata = result[0]
        assert "Hello, world!" in text
        assert "section" in metadata

    def test_extract_text_empty_file_returns_empty(self, parser: TextParser, tmp_path: Path):
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        result = parser.extract_text(test_file)

        assert result == []

    def test_handles_missing_file(self, parser: TextParser):
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.txt"))

    def test_extract_text_handles_missing_file(self, parser: TextParser):
        with pytest.raises(FileNotFoundError):
            parser.extract_text(Path("/nonexistent/file.txt"))
