"""Markdown document parser."""

import re
from pathlib import Path

from src.domain.entities import Book
from src.domain.interfaces import DocumentParser


class MarkdownParser(DocumentParser):
    """Parser for Markdown (.md) files."""

    def parse(self, file_path: Path) -> Book:
        """
        Parse a Markdown file.

        Args:
            file_path: Path to .md file.

        Returns:
            Book entity with extracted content.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract title from first H1 or filename
        title = self._extract_title(content, file_path)

        # Extract author from frontmatter if present
        author = self._extract_author(content)

        return Book(
            title=title,
            author=author,
            file_type="md",
            content=content,
        )

    def _extract_title(self, content: str, file_path: Path) -> str:
        """Extract title from first H1 heading or use filename."""
        # Try to find first H1 heading (# Title or Title\n===)
        h1_hash = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_hash:
            return h1_hash.group(1).strip()

        h1_underline = re.search(r"^(.+)\n={3,}\s*$", content, re.MULTILINE)
        if h1_underline:
            return h1_underline.group(1).strip()

        # Fallback to filename without extension
        return file_path.stem

    def _extract_author(self, content: str) -> str | None:
        """Extract author from YAML frontmatter if present."""
        # Check for YAML frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            # Look for author field
            author_match = re.search(r"^author:\s*(.+)$", frontmatter, re.MULTILINE)
            if author_match:
                return author_match.group(1).strip().strip('"\'')

        return None
