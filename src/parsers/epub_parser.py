"""EPUB document parser."""

from pathlib import Path

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

from .base import DocumentParser


class EpubParser(DocumentParser):
    """Parses EPUB files using ebooklib."""

    def parse(self, file_path: Path) -> tuple[str, str | None]:
        """Extract title and author from EPUB metadata."""
        if not file_path.exists():
            raise FileNotFoundError(f"EPUB not found: {file_path}")

        book = epub.read_epub(str(file_path), options={"ignore_ncx": True})

        title = book.get_metadata("DC", "title")
        title = title[0][0] if title else file_path.stem

        author = book.get_metadata("DC", "creator")
        author = author[0][0] if author else None

        return str(title), str(author) if author else None

    def extract_text(self, file_path: Path) -> list[tuple[str, dict]]:
        """
        Extract text from each chapter.

        Returns:
            List of (chapter_text, {"chapter": str}) tuples.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"EPUB not found: {file_path}")

        book = epub.read_epub(str(file_path), options={"ignore_ncx": True})
        chapters = []
        chapter_num = 0

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content()
                soup = BeautifulSoup(content, "html.parser")
                text = soup.get_text(separator="\n", strip=True)

                if text.strip():
                    chapter_num += 1
                    # Try to get chapter title from first heading
                    heading = soup.find(["h1", "h2", "h3"])
                    chapter_name = (
                        heading.get_text(strip=True) if heading else f"Chapter {chapter_num}"
                    )

                    chapters.append((text, {"chapter": chapter_name}))

        return chapters
