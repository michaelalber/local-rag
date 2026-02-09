"""Document parsing."""

from .base import DocumentParser
from .chunker import TextChunker
from .epub_parser import EpubParser
from .factory import DOCLING_EXTENSIONS, get_parser
from .html_parser import HTMLParser
from .markdown_parser import MarkdownParser
from .pdf_parser import PdfParser
from .rst_parser import ReStructuredTextParser
from .text_parser import TextParser
from .validator import FileValidator

__all__ = [
    "DOCLING_EXTENSIONS",
    "DocumentParser",
    "EpubParser",
    "FileValidator",
    "HTMLParser",
    "MarkdownParser",
    "PdfParser",
    "ReStructuredTextParser",
    "TextChunker",
    "TextParser",
    "get_parser",
]

# Conditional export for DoclingParser (only when docling is installed)
try:
    from .docling_parser import DoclingParser  # noqa: F401

    __all__.append("DoclingParser")
except ImportError:
    pass
