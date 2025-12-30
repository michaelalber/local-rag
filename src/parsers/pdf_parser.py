"""PDF document parser."""

from pathlib import Path

from pypdf import PdfReader

from .base import DocumentParser


class PdfParser(DocumentParser):
    """Parses PDF files using pypdf."""

    def parse(self, file_path: Path) -> tuple[str, str | None]:
        """Extract title and author from PDF metadata."""
        reader = PdfReader(file_path)
        metadata = reader.metadata or {}

        title = metadata.get("/Title", file_path.stem) or file_path.stem
        author = metadata.get("/Author")

        return str(title), str(author) if author else None

    def extract_text(self, file_path: Path) -> list[tuple[str, dict]]:
        """
        Extract text from each page.

        Returns:
            List of (page_text, {"page_number": int}) tuples.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        reader = PdfReader(file_path)
        pages = []

        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append((text, {"page_number": i}))

        return pages
