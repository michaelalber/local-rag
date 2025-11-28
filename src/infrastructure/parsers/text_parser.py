"""Plain text document parser."""

from pathlib import Path

from src.domain.entities import Book
from src.domain.interfaces import DocumentParser


class TextParser(DocumentParser):
    """Parser for plain text (.txt) files."""

    def parse(self, file_path: Path) -> Book:
        """
        Parse a plain text file.

        Args:
            file_path: Path to .txt file.

        Returns:
            Book entity with extracted content.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Use filename as title (no metadata in plain text)
        title = file_path.stem

        return Book(
            title=title,
            author=None,
            file_type="txt",
            content=content,
        )
