"""Markdown document parser."""

import re
from pathlib import Path

from .base import DocumentParser


class MarkdownParser(DocumentParser):
    """Parser for Markdown (.md) files."""

    def parse(self, file_path: Path) -> tuple[str, str | None]:
        """
        Extract title and author from Markdown file.

        Args:
            file_path: Path to .md file.

        Returns:
            Tuple of (title, author). Author may be None.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        title = self._extract_title(content, file_path)
        author = self._extract_author(content)

        return title, author

    def extract_text(self, file_path: Path) -> list[tuple[str, dict]]:
        """
        Extract text from Markdown file, split by sections.

        Args:
            file_path: Path to .md file.

        Returns:
            List of (text, metadata) tuples with section info.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Remove YAML frontmatter if present
        content = re.sub(r"^---\n.*?\n---\n?", "", content, flags=re.DOTALL)

        if not content.strip():
            return []

        # Split by headings (## or more)
        sections = re.split(r"^(#{1,6}\s+.+)$", content, flags=re.MULTILINE)

        results = []
        current_section = "Introduction"

        for i, part in enumerate(sections):
            if re.match(r"^#{1,6}\s+", part):
                # This is a heading
                current_section = re.sub(r"^#{1,6}\s+", "", part).strip()
            elif part.strip():
                results.append((part.strip(), {"section": current_section}))

        return results if results else [(content.strip(), {"section": "content"})]

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
