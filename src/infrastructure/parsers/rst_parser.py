"""ReStructuredText document parser."""

import re
from pathlib import Path

from src.domain.entities import Book
from src.domain.interfaces import DocumentParser


class ReStructuredTextParser(DocumentParser):
    """Parser for ReStructuredText (.rst) files."""

    def parse(self, file_path: Path) -> Book:
        """
        Parse a ReStructuredText file.

        Args:
            file_path: Path to .rst file.

        Returns:
            Book entity with extracted content.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract title from first heading
        title = self._extract_title(content, file_path)

        # Extract author from field list if present
        author = self._extract_author(content)

        return Book(
            title=title,
            author=author,
            file_type="rst",
            content=content,
        )

    def _extract_title(self, content: str, file_path: Path) -> str:
        """Extract title from first RST heading."""
        # RST headings are text with underline (and optional overline)
        # Common underline characters: = - ` : ' " ~ ^ _ * + # < >

        # Pattern for overline and underline style
        overline_pattern = r"^([=\-`:'\"~^_*+#<>])\1+\n(.+)\n\1\1+\s*$"
        match = re.search(overline_pattern, content, re.MULTILINE)
        if match:
            return match.group(2).strip()

        # Pattern for underline only style
        underline_pattern = r"^(.+)\n([=\-`:'\"~^_*+#<>])\2+\s*$"
        match = re.search(underline_pattern, content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Fallback to filename
        return file_path.stem

    def _extract_author(self, content: str) -> str | None:
        """Extract author from RST field list."""
        # Look for :Author: field at the beginning of the document
        author_match = re.search(r"^:Author:\s*(.+)$", content, re.MULTILINE)
        if author_match:
            return author_match.group(1).strip()

        return None
