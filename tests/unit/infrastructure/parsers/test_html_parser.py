"""Tests for HTML parsing."""

from pathlib import Path

import pytest

from src.infrastructure.parsers.html_parser import HTMLParser


class TestHTMLParser:
    @pytest.fixture
    def parser(self) -> HTMLParser:
        return HTMLParser()

    def test_parse_extracts_title_from_title_tag(self, parser: HTMLParser, tmp_path: Path):
        test_file = tmp_path / "test.html"
        test_file.write_text("""<!DOCTYPE html>
<html>
<head><title>My Page Title</title></head>
<body><p>Content</p></body>
</html>
""")

        title, author = parser.parse(test_file)

        assert title == "My Page Title"

    def test_parse_extracts_author_from_meta(self, parser: HTMLParser, tmp_path: Path):
        test_file = tmp_path / "test.html"
        test_file.write_text("""<!DOCTYPE html>
<html>
<head>
    <title>Document</title>
    <meta name="author" content="Jane Smith">
</head>
<body><p>Content</p></body>
</html>
""")

        title, author = parser.parse(test_file)

        assert author == "Jane Smith"

    def test_parse_uses_h1_when_no_title(self, parser: HTMLParser, tmp_path: Path):
        test_file = tmp_path / "test.html"
        test_file.write_text("""<html>
<body>
<h1>Main Heading</h1>
<p>Content</p>
</body>
</html>
""")

        title, author = parser.parse(test_file)

        assert title == "Main Heading"

    def test_parse_uses_filename_as_fallback(self, parser: HTMLParser, tmp_path: Path):
        test_file = tmp_path / "my_page.html"
        test_file.write_text("<p>Just some content.</p>")

        title, author = parser.parse(test_file)

        assert title == "my_page"

    def test_extract_text_strips_html_tags(self, parser: HTMLParser, tmp_path: Path):
        test_file = tmp_path / "test.html"
        test_file.write_text("""<html>
<body>
<p>Hello <strong>world</strong>!</p>
<script>console.log('ignored');</script>
</body>
</html>
""")

        result = parser.extract_text(test_file)

        assert len(result) == 1
        text, _ = result[0]
        assert "Hello" in text
        assert "world" in text
        assert "<strong>" not in text
        assert "console.log" not in text

    def test_extract_text_empty_file_returns_empty(self, parser: HTMLParser, tmp_path: Path):
        test_file = tmp_path / "empty.html"
        test_file.write_text("")

        result = parser.extract_text(test_file)

        assert result == []

    def test_handles_missing_file(self, parser: HTMLParser):
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.html"))

    def test_extract_text_handles_missing_file(self, parser: HTMLParser):
        with pytest.raises(FileNotFoundError):
            parser.extract_text(Path("/nonexistent/file.html"))
