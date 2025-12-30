"""Plain text document parser."""

from pathlib import Path

from .base import DocumentParser


class TextParser(DocumentParser):
    """Parser for plain text (.txt) files."""

    def parse(self, file_path: Path) -> tuple[str, str | None]:
        """
        Extract title and author from plain text file.

        Args:
            file_path: Path to .txt file.

        Returns:
            Tuple of (title, author). Author is always None for plain text.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Text file not found: {file_path}")

        # Use filename as title (no metadata in plain text)
        title = file_path.stem
        return title, None

    def extract_text(self, file_path: Path) -> list[tuple[str, dict]]:
        """
        Extract text from plain text file.

        Args:
            file_path: Path to .txt file.

        Returns:
            List of (text, metadata) tuples. Single entry for entire file.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Text file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return []

        return [(content, {"section": "content"})]
