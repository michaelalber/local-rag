"""Tests for Markdown parsing."""

from pathlib import Path

import pytest
from src.parsers import MarkdownParser


class TestMarkdownParser:
    @pytest.fixture
    def parser(self) -> MarkdownParser:
        return MarkdownParser()

    def test_parse_extracts_title_from_h1(self, parser: MarkdownParser, tmp_path: Path):
        test_file = tmp_path / "test.md"
        test_file.write_text("# My Document Title\n\nSome content here.")

        title, author = parser.parse(test_file)

        assert title == "My Document Title"
        assert author is None

    def test_parse_extracts_author_from_frontmatter(self, parser: MarkdownParser, tmp_path: Path):
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
author: John Doe
---

# My Document

Content here.
""")

        title, author = parser.parse(test_file)

        assert title == "My Document"
        assert author == "John Doe"

    def test_parse_uses_filename_when_no_h1(self, parser: MarkdownParser, tmp_path: Path):
        test_file = tmp_path / "my_notes.md"
        test_file.write_text("Just some text without a heading.")

        title, _author = parser.parse(test_file)

        assert title == "my_notes"

    def test_extract_text_splits_by_sections(self, parser: MarkdownParser, tmp_path: Path):
        test_file = tmp_path / "test.md"
        test_file.write_text("""# Introduction

This is the intro.

## Chapter 1

First chapter content.

## Chapter 2

Second chapter content.
""")

        result = parser.extract_text(test_file)

        assert len(result) >= 1
        # Check that sections are captured in metadata
        sections = [metadata.get("section") for _, metadata in result]
        assert "Introduction" in sections or "Chapter 1" in sections

    def test_extract_text_removes_frontmatter(self, parser: MarkdownParser, tmp_path: Path):
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
author: Jane
date: 2024-01-01
---

# Title

Content here.
""")

        result = parser.extract_text(test_file)

        # Frontmatter should be removed from content
        all_text = " ".join(text for text, _ in result)
        assert "author: Jane" not in all_text
        assert "Content here" in all_text

    def test_extract_text_empty_file_returns_empty(self, parser: MarkdownParser, tmp_path: Path):
        test_file = tmp_path / "empty.md"
        test_file.write_text("")

        result = parser.extract_text(test_file)

        assert result == []

    def test_handles_missing_file(self, parser: MarkdownParser):
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.md"))
