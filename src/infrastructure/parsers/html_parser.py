"""HTML document parser."""

import re
from pathlib import Path

from src.domain.entities import Book
from src.domain.interfaces import DocumentParser


class HTMLParser(DocumentParser):
    """Parser for HTML (.html) files."""

    def parse(self, file_path: Path) -> Book:
        """
        Parse an HTML file.

        Args:
            file_path: Path to .html file.

        Returns:
            Book entity with extracted content.
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            # Fallback to basic HTML stripping if BeautifulSoup not available
            return self._parse_without_bs4(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # Extract title from <title> tag or first <h1>
        title = self._extract_title_bs4(soup, file_path)

        # Extract author from meta tag if present
        author = self._extract_author_bs4(soup)

        # Get text content, preserving code blocks
        content = self._extract_content_bs4(soup)

        return Book(
            title=title,
            author=author,
            file_type="html",
            content=content,
        )

    def _extract_title_bs4(self, soup, file_path: Path) -> str:
        """Extract title from HTML using BeautifulSoup."""
        # Try <title> tag first
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        # Try first <h1>
        h1_tag = soup.find("h1")
        if h1_tag:
            return h1_tag.get_text().strip()

        # Fallback to filename
        return file_path.stem

    def _extract_author_bs4(self, soup) -> str | None:
        """Extract author from HTML meta tags."""
        # Look for meta author tag
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta and author_meta.get("content"):
            return author_meta.get("content").strip()

        return None

    def _extract_content_bs4(self, soup) -> str:
        """Extract text content from HTML, preserving code blocks."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()

        # Get text with some structure preserved
        # Replace code blocks with markers to preserve them
        for code_tag in soup.find_all(["pre", "code"]):
            code_text = code_tag.get_text()
            code_tag.string = f"\n```\n{code_text}\n```\n"

        # Get all text
        text = soup.get_text(separator="\n")

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line)

        return text

    def _parse_without_bs4(self, file_path: Path) -> Book:
        """Fallback parser without BeautifulSoup."""
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Extract title from <title> tag
        title_match = re.search(r"<title>(.*?)</title>", html_content, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else file_path.stem

        # Basic HTML tag removal
        text = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)

        # Decode HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")
        text = text.replace("&quot;", '"')

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        content = "\n".join(line for line in lines if line)

        return Book(
            title=title,
            author=None,
            file_type="html",
            content=content,
        )
