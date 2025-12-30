"""HTML document parser."""

import re
from pathlib import Path

from src.domain.interfaces import DocumentParser


class HTMLParser(DocumentParser):
    """Parser for HTML (.html) files."""

    def parse(self, file_path: Path) -> tuple[str, str | None]:
        """
        Extract title and author from HTML file.

        Args:
            file_path: Path to .html file.

        Returns:
            Tuple of (title, author). Author may be None.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"HTML file not found: {file_path}")

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return self._parse_without_bs4(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")
        title = self._extract_title_bs4(soup, file_path)
        author = self._extract_author_bs4(soup)

        return title, author

    def extract_text(self, file_path: Path) -> list[tuple[str, dict]]:
        """
        Extract text from HTML file.

        Args:
            file_path: Path to .html file.

        Returns:
            List of (text, metadata) tuples with section info.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"HTML file not found: {file_path}")

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return self._extract_text_without_bs4(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")
        content = self._extract_content_bs4(soup)

        if not content.strip():
            return []

        return [(content, {"section": "content"})]

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

    def _parse_without_bs4(self, file_path: Path) -> tuple[str, str | None]:
        """Fallback parser without BeautifulSoup."""
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Extract title from <title> tag
        title_match = re.search(r"<title>(.*?)</title>", html_content, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else file_path.stem

        return title, None

    def _extract_text_without_bs4(self, file_path: Path) -> list[tuple[str, dict]]:
        """Fallback text extraction without BeautifulSoup."""
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

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

        if not content.strip():
            return []

        return [(content, {"section": "content"})]
