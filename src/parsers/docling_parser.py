"""Document parser using Docling for enhanced PDF and Office document support."""

from pathlib import Path
from typing import TYPE_CHECKING

from .base import DocumentParser

if TYPE_CHECKING:
    from docling.chunking import HybridChunker
    from docling.document_converter import DocumentConverter


class DoclingParser(DocumentParser):
    """Parser using Docling for structure-aware document processing.

    Supports: PDF, DOCX, PPTX, XLSX, images (with OCR)

    Features:
    - High-accuracy table extraction
    - Heading hierarchy preservation
    - Token-based chunking aligned with embedding models
    """

    def __init__(self) -> None:
        self._converter: DocumentConverter | None = None
        self._chunker: HybridChunker | None = None

    def _ensure_docling(self) -> None:
        """Lazy-load docling to fail gracefully if not installed."""
        if self._converter is None:
            try:
                from docling.chunking import HybridChunker
                from docling.document_converter import DocumentConverter

                self._converter = DocumentConverter()
                self._chunker = HybridChunker(
                    tokenizer="sentence-transformers/all-MiniLM-L6-v2",
                    max_tokens=512,
                )
            except ImportError as e:
                raise ImportError(
                    "Docling required for enhanced parsing. "
                    "Install with: pip install localbookchat[enhanced]"
                ) from e

    def parse(self, file_path: Path) -> tuple[str, str | None]:
        """
        Extract title and author from document.

        Args:
            file_path: Path to the document file.

        Returns:
            Tuple of (title, author). Author may be None.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        self._ensure_docling()
        assert self._converter is not None  # Set by _ensure_docling  # nosec B101
        result = self._converter.convert(file_path)
        doc = result.document

        # Try to extract title from document metadata
        title = file_path.stem
        if hasattr(doc, "name") and doc.name:
            title = doc.name

        # Author extraction varies by document type
        author = None

        return str(title), author

    def extract_text(self, file_path: Path) -> list[tuple[str, dict]]:
        """
        Extract text segments with structural metadata.

        Uses Docling's HybridChunker for intelligent, token-based chunking
        that preserves document structure.

        Args:
            file_path: Path to the document file.

        Returns:
            List of (text, metadata) tuples with page numbers and sections.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        self._ensure_docling()
        assert self._converter is not None  # Set by _ensure_docling  # nosec B101
        assert self._chunker is not None  # Set by _ensure_docling  # nosec B101
        result = self._converter.convert(file_path)
        doc = result.document

        chunks = list(self._chunker.chunk(doc))
        segments = []

        for chunk in chunks:
            metadata: dict = {}

            # Extract metadata from chunk if available
            if hasattr(chunk, "meta") and chunk.meta:
                # Page number
                if hasattr(chunk.meta, "page"):
                    metadata["page_number"] = chunk.meta.page

                # Section hierarchy (list of heading titles)
                if hasattr(chunk.meta, "headings") and chunk.meta.headings:
                    headings = list(chunk.meta.headings)
                    metadata["section_hierarchy"] = headings
                    if headings:
                        metadata["section"] = headings[-1]

            # Only include non-empty text
            text = chunk.text.strip() if hasattr(chunk, "text") else ""
            if text:
                segments.append((text, metadata))

        return segments
