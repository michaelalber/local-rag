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
    "DocumentParser",
    "FileValidator",
    "TextChunker",
    "PdfParser",
    "EpubParser",
    "MarkdownParser",
    "TextParser",
    "ReStructuredTextParser",
    "HTMLParser",
    "get_parser",
    "DOCLING_EXTENSIONS",
]

# Conditional export for DoclingParser (only when docling is installed)
try:
    from .docling_parser import DoclingParser

    __all__.append("DoclingParser")
except ImportError:
    pass
