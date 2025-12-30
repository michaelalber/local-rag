"""ReStructuredText document parser."""

import re
from pathlib import Path

from .base import DocumentParser


class ReStructuredTextParser(DocumentParser):
    """Parser for ReStructuredText (.rst) files."""

    def parse(self, file_path: Path) -> tuple[str, str | None]:
        """
        Extract title and author from ReStructuredText file.

        Args:
            file_path: Path to .rst file.

        Returns:
            Tuple of (title, author). Author may be None.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"RST file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        title = self._extract_title(content, file_path)
        author = self._extract_author(content)

        return title, author

    def extract_text(self, file_path: Path) -> list[tuple[str, dict]]:
        """
        Extract text from ReStructuredText file.

        Args:
            file_path: Path to .rst file.

        Returns:
            List of (text, metadata) tuples with section info.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"RST file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return []

        return [(content, {"section": "content"})]

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
