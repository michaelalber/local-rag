"""Parser factory for selecting appropriate parser."""

from pathlib import Path

from src.domain.exceptions import UnsupportedFileTypeError
from src.domain.interfaces import DocumentParser

from .epub_parser import EpubParser
from .pdf_parser import PdfParser


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
    }

    parser_class = parsers.get(ext)
    if parser_class is None:
        raise UnsupportedFileTypeError(f"No parser for file type: {ext}")

    return parser_class()
