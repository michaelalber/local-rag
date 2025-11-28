"""File validation with OWASP security considerations."""

import re
from pathlib import Path

from src.domain.exceptions import FileSizeLimitError, UnsupportedFileTypeError


class FileValidator:
    """Validates uploaded files for security and compatibility."""

    ALLOWED_EXTENSIONS = {".pdf", ".epub", ".md", ".txt", ".rst", ".html", ".htm"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "application/epub+zip",
        "text/markdown",
        "text/plain",
        "text/x-rst",
        "text/html",
    }

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
            raise UnsupportedFileTypeError(f"Suspicious filename pattern: {file_path.name}")

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
