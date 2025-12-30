"""Tests for ReStructuredText parsing."""

from pathlib import Path

import pytest

from src.parsers import ReStructuredTextParser


class TestReStructuredTextParser:
    @pytest.fixture
    def parser(self) -> ReStructuredTextParser:
        return ReStructuredTextParser()

    def test_parse_extracts_title_from_underline_heading(
        self, parser: ReStructuredTextParser, tmp_path: Path
    ):
        test_file = tmp_path / "test.rst"
        test_file.write_text("""My Document Title
=================

Some content here.
""")

        title, author = parser.parse(test_file)

        assert title == "My Document Title"
        assert author is None

    def test_parse_extracts_title_from_overline_heading(
        self, parser: ReStructuredTextParser, tmp_path: Path
    ):
        test_file = tmp_path / "test.rst"
        test_file.write_text("""=================
My Document Title
=================

Some content here.
""")

        title, author = parser.parse(test_file)

        assert title == "My Document Title"

    def test_parse_extracts_author_from_field(
        self, parser: ReStructuredTextParser, tmp_path: Path
    ):
        test_file = tmp_path / "test.rst"
        test_file.write_text(""":Author: John Doe

Title
=====

Content here.
""")

        title, author = parser.parse(test_file)

        assert author == "John Doe"

    def test_parse_uses_filename_when_no_heading(
        self, parser: ReStructuredTextParser, tmp_path: Path
    ):
        test_file = tmp_path / "my_notes.rst"
        test_file.write_text("Just some text without a heading.")

        title, author = parser.parse(test_file)

        assert title == "my_notes"

    def test_extract_text_returns_content(
        self, parser: ReStructuredTextParser, tmp_path: Path
    ):
        test_file = tmp_path / "test.rst"
        test_file.write_text("""Title
=====

This is the content of my RST document.
It has multiple lines.
""")

        result = parser.extract_text(test_file)

        assert len(result) == 1
        text, metadata = result[0]
        assert "content of my RST document" in text
        assert "section" in metadata

    def test_extract_text_empty_file_returns_empty(
        self, parser: ReStructuredTextParser, tmp_path: Path
    ):
        test_file = tmp_path / "empty.rst"
        test_file.write_text("")

        result = parser.extract_text(test_file)

        assert result == []

    def test_handles_missing_file(self, parser: ReStructuredTextParser):
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.rst"))

    def test_extract_text_handles_missing_file(self, parser: ReStructuredTextParser):
        with pytest.raises(FileNotFoundError):
            parser.extract_text(Path("/nonexistent/file.rst"))
