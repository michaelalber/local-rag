"""Parser factory for selecting appropriate parser."""

from pathlib import Path

from src.models import UnsupportedFileTypeError

from .base import DocumentParser

from .epub_parser import EpubParser
from .html_parser import HTMLParser
from .markdown_parser import MarkdownParser
from .pdf_parser import PdfParser
from .rst_parser import ReStructuredTextParser
from .text_parser import TextParser


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

    parsers = {
        ".pdf": PdfParser,
        ".epub": EpubParser,
        ".md": MarkdownParser,
        ".txt": TextParser,
        ".rst": ReStructuredTextParser,
        ".html": HTMLParser,
        ".htm": HTMLParser,  # .htm also maps to HTMLParser
    }

    parser_class = parsers.get(ext)
    if parser_class is None:
        raise UnsupportedFileTypeError(f"No parser for file type: {ext}")

    return parser_class()
