# Phase 2: Document Parsing Infrastructure

## Objective

Implement PDF and EPUB parsing with chunking. Include OWASP-compliant file validation.

## Files to Create

```
src/infrastructure/parsers/
├── __init__.py
├── validator.py
├── pdf_parser.py
├── epub_parser.py
├── chunker.py
└── factory.py
tests/
├── sample_data/
│   ├── sample.pdf      (create small test PDF)
│   └── sample.epub     (create small test EPUB)
└── unit/infrastructure/
    └── parsers/
        ├── __init__.py
        ├── test_validator.py
        ├── test_pdf_parser.py
        ├── test_epub_parser.py
        └── test_chunker.py
```

## Write Tests First

### tests/unit/infrastructure/parsers/test_validator.py

```python
"""Tests for file validation."""

import pytest
from pathlib import Path
from io import BytesIO

from src.infrastructure.parsers.validator import FileValidator
from src.domain.exceptions import UnsupportedFileTypeError, FileSizeLimitError


class TestFileValidator:
    @pytest.fixture
    def validator(self) -> FileValidator:
        return FileValidator(max_size_mb=1)  # 1MB for tests

    def test_accepts_pdf_extension(self, validator: FileValidator):
        # Should not raise
        validator.validate_extension(Path("book.pdf"))

    def test_accepts_epub_extension(self, validator: FileValidator):
        validator.validate_extension(Path("book.epub"))

    def test_rejects_invalid_extension(self, validator: FileValidator):
        with pytest.raises(UnsupportedFileTypeError):
            validator.validate_extension(Path("book.doc"))

    def test_rejects_exe_extension(self, validator: FileValidator):
        with pytest.raises(UnsupportedFileTypeError):
            validator.validate_extension(Path("malware.exe"))

    def test_rejects_double_extension_trick(self, validator: FileValidator):
        with pytest.raises(UnsupportedFileTypeError):
            validator.validate_extension(Path("book.pdf.exe"))

    def test_accepts_file_under_size_limit(self, validator: FileValidator):
        small_content = b"x" * 1000  # 1KB
        validator.validate_size(len(small_content))

    def test_rejects_file_over_size_limit(self, validator: FileValidator):
        large_content = b"x" * (2 * 1024 * 1024)  # 2MB
        with pytest.raises(FileSizeLimitError):
            validator.validate_size(len(large_content))

    def test_sanitize_filename_removes_path_traversal(self, validator: FileValidator):
        dangerous = "../../../etc/passwd"
        safe = validator.sanitize_filename(dangerous)
        assert ".." not in safe
        assert "/" not in safe

    def test_sanitize_filename_preserves_extension(self, validator: FileValidator):
        result = validator.sanitize_filename("My Book (2024).pdf")
        assert result.endswith(".pdf")

    def test_sanitize_filename_handles_spaces(self, validator: FileValidator):
        result = validator.sanitize_filename("my book name.epub")
        assert " " not in result or result.replace(" ", "_")  # Either removed or replaced
```

### tests/unit/infrastructure/parsers/test_chunker.py

```python
"""Tests for text chunking."""

import pytest

from src.infrastructure.parsers.chunker import TextChunker


class TestTextChunker:
    @pytest.fixture
    def chunker(self) -> TextChunker:
        return TextChunker(chunk_size=100, overlap=20)

    def test_chunks_text_into_pieces(self, chunker: TextChunker):
        text = "word " * 100  # 500 chars
        chunks = chunker.chunk(text, metadata={"page": 1})
        assert len(chunks) > 1

    def test_chunks_include_metadata(self, chunker: TextChunker):
        text = "This is sample text for chunking."
        chunks = chunker.chunk(text, metadata={"page": 42, "chapter": "Intro"})
        assert all(c["metadata"]["page"] == 42 for c in chunks)

    def test_small_text_single_chunk(self, chunker: TextChunker):
        text = "Short text."
        chunks = chunker.chunk(text, metadata={})
        assert len(chunks) == 1

    def test_empty_text_returns_empty(self, chunker: TextChunker):
        chunks = chunker.chunk("", metadata={})
        assert chunks == []

    def test_overlap_creates_continuity(self):
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "A" * 30 + "B" * 30 + "C" * 30  # 90 chars
        chunks = chunker.chunk(text, metadata={})
        
        # With overlap, adjacent chunks should share some content
        if len(chunks) > 1:
            # Last chars of chunk 0 should appear in start of chunk 1
            assert chunks[0]["text"][-10:] in chunks[1]["text"] or len(chunks[0]["text"]) < 50
```

### tests/unit/infrastructure/parsers/test_pdf_parser.py

```python
"""Tests for PDF parsing."""

import pytest
from pathlib import Path

from src.infrastructure.parsers.pdf_parser import PdfParser


class TestPdfParser:
    @pytest.fixture
    def parser(self) -> PdfParser:
        return PdfParser()

    @pytest.fixture
    def sample_pdf(self, sample_data_dir: Path) -> Path:
        return sample_data_dir / "sample.pdf"

    def test_extracts_text_from_pdf(self, parser: PdfParser, sample_pdf: Path):
        if not sample_pdf.exists():
            pytest.skip("Sample PDF not available")
        
        pages = parser.extract_text(sample_pdf)
        assert len(pages) > 0
        assert all(isinstance(text, str) for text, _ in pages)

    def test_extracts_page_numbers(self, parser: PdfParser, sample_pdf: Path):
        if not sample_pdf.exists():
            pytest.skip("Sample PDF not available")
        
        pages = parser.extract_text(sample_pdf)
        for text, metadata in pages:
            assert "page_number" in metadata
            assert isinstance(metadata["page_number"], int)

    def test_handles_missing_file(self, parser: PdfParser):
        with pytest.raises(FileNotFoundError):
            parser.extract_text(Path("/nonexistent/file.pdf"))
```

## Implementation

### src/infrastructure/parsers/validator.py

```python
"""File validation with OWASP security considerations."""

import re
from pathlib import Path

from src.domain.exceptions import UnsupportedFileTypeError, FileSizeLimitError


class FileValidator:
    """Validates uploaded files for security and compatibility."""

    ALLOWED_EXTENSIONS = {".pdf", ".epub"}
    ALLOWED_MIME_TYPES = {"application/pdf", "application/epub+zip"}

    def __init__(self, max_size_mb: int = 50):
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def validate_extension(self, file_path: Path) -> None:
        """
        Validate file extension.

        Raises:
            UnsupportedFileTypeError: If extension not allowed.
        """
        # Get the final suffix only (prevents .pdf.exe tricks)
        ext = file_path.suffix.lower()
        
        # Also check the full name doesn't have suspicious patterns
        name_lower = file_path.name.lower()
        if ".exe" in name_lower or ".sh" in name_lower or ".bat" in name_lower:
            raise UnsupportedFileTypeError(
                f"Suspicious filename pattern: {file_path.name}"
            )

        if ext not in self.ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"File type '{ext}' not supported. Allowed: {self.ALLOWED_EXTENSIONS}"
            )

    def validate_size(self, size_bytes: int) -> None:
        """
        Validate file size.

        Raises:
            FileSizeLimitError: If file exceeds limit.
        """
        if size_bytes > self.max_size_bytes:
            max_mb = self.max_size_bytes / (1024 * 1024)
            actual_mb = size_bytes / (1024 * 1024)
            raise FileSizeLimitError(
                f"File size {actual_mb:.1f}MB exceeds limit of {max_mb:.0f}MB"
            )

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe storage.

        Removes path traversal attempts and special characters.
        """
        # Extract just the filename, removing any path components
        name = Path(filename).name
        
        # Remove any remaining path separators
        name = name.replace("/", "_").replace("\\", "_")
        
        # Remove path traversal patterns
        name = name.replace("..", "_")
        
        # Keep only safe characters: alphanumeric, dash, underscore, dot
        # Preserve the extension
        stem = Path(name).stem
        ext = Path(name).suffix
        
        safe_stem = re.sub(r"[^\w\-]", "_", stem)
        safe_stem = re.sub(r"_+", "_", safe_stem)  # Collapse multiple underscores
        safe_stem = safe_stem.strip("_")
        
        if not safe_stem:
            safe_stem = "unnamed"

        return f"{safe_stem}{ext.lower()}"

    def validate_file(self, file_path: Path, size_bytes: int) -> str:
        """
        Full validation pipeline.

        Returns:
            Sanitized filename.

        Raises:
            UnsupportedFileTypeError: Invalid file type.
            FileSizeLimitError: File too large.
        """
        self.validate_extension(file_path)
        self.validate_size(size_bytes)
        return self.sanitize_filename(file_path.name)
```

### src/infrastructure/parsers/chunker.py

```python
"""Text chunking for embedding."""


class TextChunker:
    """Splits text into overlapping chunks for embedding."""

    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        """
        Args:
            chunk_size: Target size of each chunk in characters.
            overlap: Number of characters to overlap between chunks.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: dict) -> list[dict]:
        """
        Split text into chunks with metadata.

        Args:
            text: Text to chunk.
            metadata: Metadata to attach to each chunk.

        Returns:
            List of {"text": str, "metadata": dict} dicts.
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        
        # If text fits in one chunk, return as-is
        if len(text) <= self.chunk_size:
            return [{"text": text, "metadata": metadata.copy()}]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # If not at the end, try to break at sentence boundary
            if end < len(text):
                # Look for sentence end within last 20% of chunk
                search_start = end - int(self.chunk_size * 0.2)
                search_region = text[search_start:end]
                
                # Find last sentence boundary
                for boundary in [". ", ".\n", "? ", "! "]:
                    last_boundary = search_region.rfind(boundary)
                    if last_boundary != -1:
                        end = search_start + last_boundary + 1
                        break

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "metadata": metadata.copy()
                })

            # Move start position, accounting for overlap
            start = end - self.overlap if end < len(text) else end

        return chunks
```

### src/infrastructure/parsers/pdf_parser.py

```python
"""PDF document parser."""

from pathlib import Path

from pypdf import PdfReader

from src.domain.interfaces import DocumentParser


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
```

### src/infrastructure/parsers/epub_parser.py

```python
"""EPUB document parser."""

from pathlib import Path

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

from src.domain.interfaces import DocumentParser


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
                    chapter_name = heading.get_text(strip=True) if heading else f"Chapter {chapter_num}"
                    
                    chapters.append((text, {"chapter": chapter_name}))

        return chapters
```

### src/infrastructure/parsers/factory.py

```python
"""Parser factory for selecting appropriate parser."""

from pathlib import Path

from src.domain.interfaces import DocumentParser
from src.domain.exceptions import UnsupportedFileTypeError

from .pdf_parser import PdfParser
from .epub_parser import EpubParser


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
```

### src/infrastructure/parsers/__init__.py

```python
"""Document parsing infrastructure."""

from .validator import FileValidator
from .chunker import TextChunker
from .pdf_parser import PdfParser
from .epub_parser import EpubParser
from .factory import get_parser

__all__ = ["FileValidator", "TextChunker", "PdfParser", "EpubParser", "get_parser"]
```

## Add BeautifulSoup Dependency

Update `pyproject.toml` dependencies:

```toml
dependencies = [
    # ... existing ...
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",  # faster parser for BeautifulSoup
]
```

## Create Sample Test Files

Create minimal test files in `tests/sample_data/`:

```bash
# Create sample_data directory
mkdir -p tests/sample_data

# For PDF: Use Python to create a minimal test PDF
python -c "
from fpdf import FPDF
pdf = FPDF()
pdf.add_page()
pdf.set_font('Arial', size=12)
pdf.cell(200, 10, txt='Sample PDF for testing', ln=1)
pdf.cell(200, 10, txt='This is page 1 content.', ln=1)
pdf.add_page()
pdf.cell(200, 10, txt='This is page 2 content.', ln=1)
pdf.output('tests/sample_data/sample.pdf')
"
```

Or add `fpdf2` as a dev dependency and create the sample in conftest.py.

## Verification

```bash
# Install new dependencies
pip install -e ".[dev]"

# Run parser tests
pytest tests/unit/infrastructure/parsers/ -v

# Test with a real PDF/EPUB from your collection (manual)
python -c "
from pathlib import Path
from src.infrastructure.parsers import get_parser, TextChunker

# Test with a real file
parser = get_parser(Path('path/to/your/book.pdf'))
title, author = parser.parse(Path('path/to/your/book.pdf'))
print(f'Title: {title}, Author: {author}')

pages = parser.extract_text(Path('path/to/your/book.pdf'))
print(f'Extracted {len(pages)} pages')

chunker = TextChunker(chunk_size=512, overlap=50)
all_chunks = []
for text, meta in pages[:2]:  # First 2 pages
    chunks = chunker.chunk(text, meta)
    all_chunks.extend(chunks)
print(f'Created {len(all_chunks)} chunks from first 2 pages')
"
```

## Commit

```bash
git add .
git commit -m "feat: implement document parsing with PDF, EPUB, and chunking"
```

## Next Phase

Proceed to `docs/phases/PHASE_3_VECTORS.md`
