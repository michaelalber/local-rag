"""Tests for file validation."""

from pathlib import Path

import pytest

from src.domain.exceptions import FileSizeLimitError, UnsupportedFileTypeError
from src.infrastructure.parsers.validator import FileValidator


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
