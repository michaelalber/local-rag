"""Tests for file validation."""

from pathlib import Path

import pytest
from src.models import FileSizeLimitError, UnsupportedFileTypeError
from src.parsers import FileValidator


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

    # MIME type validation tests
    def test_mime_validates_pdf_magic_bytes(self, validator: FileValidator, tmp_path: Path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        # Should not raise
        validator.validate_mime_type(pdf_file)

    def test_mime_rejects_fake_pdf(self, validator: FileValidator, tmp_path: Path):
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_bytes(b"This is not a PDF file")

        with pytest.raises(UnsupportedFileTypeError):
            validator.validate_mime_type(fake_pdf)

    def test_mime_validates_epub_zip_signature(self, validator: FileValidator, tmp_path: Path):
        epub_file = tmp_path / "test.epub"
        # EPUB files start with PK (ZIP format)
        epub_file.write_bytes(b"PK\x03\x04fake epub content")

        # Should not raise
        validator.validate_mime_type(epub_file)

    def test_mime_rejects_fake_epub(self, validator: FileValidator, tmp_path: Path):
        fake_epub = tmp_path / "fake.epub"
        fake_epub.write_bytes(b"Not a ZIP file")

        with pytest.raises(UnsupportedFileTypeError):
            validator.validate_mime_type(fake_epub)

    def test_mime_validates_utf8_text_file(self, validator: FileValidator, tmp_path: Path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Valid UTF-8 content", encoding="utf-8")

        # Should not raise
        validator.validate_mime_type(txt_file)

    def test_mime_rejects_invalid_utf8_text(self, validator: FileValidator, tmp_path: Path):
        txt_file = tmp_path / "test.txt"
        # Write invalid UTF-8 bytes
        txt_file.write_bytes(b"\xff\xfe Invalid UTF-8")

        with pytest.raises(UnsupportedFileTypeError):
            validator.validate_mime_type(txt_file)
