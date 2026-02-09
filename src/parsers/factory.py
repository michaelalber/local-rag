"""Parser factory for selecting appropriate parser."""

import os
from pathlib import Path

from src.models import UnsupportedFileTypeError

from .base import DocumentParser
from .epub_parser import EpubParser
from .html_parser import HTMLParser
from .markdown_parser import MarkdownParser
from .pdf_parser import PdfParser
from .rst_parser import ReStructuredTextParser
from .text_parser import TextParser


def _is_docling_enabled() -> bool:
    """Check if docling parser is enabled via environment variable."""
    return os.environ.get("USE_DOCLING_PARSER", "").lower() in ("true", "1", "yes")


def _get_docling_parser() -> type[DocumentParser]:
    """
    Get DoclingParser class, raising helpful error if not installed.

    Returns:
        DoclingParser class.

    Raises:
        ImportError: If docling is not installed.
    """
    from .docling_parser import DoclingParser

    return DoclingParser


# Extensions that require docling
DOCLING_EXTENSIONS = {
    ".docx",
    ".pptx",
    ".xlsx",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".tif",
}


def get_parser(file_path: Path) -> DocumentParser:
    """
    Get appropriate parser for file type.

    Args:
        file_path: Path to document.

    Returns:
        Parser instance.

    Raises:
        UnsupportedFileTypeError: If no parser for file type.
    """
    ext = file_path.suffix.lower()
    use_docling = _is_docling_enabled()

    # Standard parsers (always available)
    standard_parsers: dict[str, type[DocumentParser]] = {
        ".epub": EpubParser,
        ".md": MarkdownParser,
        ".txt": TextParser,
        ".rst": ReStructuredTextParser,
        ".html": HTMLParser,
        ".htm": HTMLParser,
    }

    # Check for docling-only extensions first
    if ext in DOCLING_EXTENSIONS:
        if not use_docling:
            raise UnsupportedFileTypeError(
                f"File type '{ext}' requires docling. "
                "Set USE_DOCLING_PARSER=true and install with: pip install localbookchat[enhanced]"
            )
        return _get_docling_parser()()

    # PDF: use docling if enabled, otherwise pypdf
    if ext == ".pdf":
        if use_docling:
            return _get_docling_parser()()
        return PdfParser()

    # Standard parsers
    parser_class = standard_parsers.get(ext)
    if parser_class is None:
        raise UnsupportedFileTypeError(f"No parser for file type: {ext}")

    return parser_class()
