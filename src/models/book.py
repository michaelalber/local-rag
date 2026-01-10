"""Book entity."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import UUID

FileType = Literal[
    # eBook formats
    "pdf", "epub",
    # Text formats
    "md", "txt", "rst", "html", "htm",
    # Office formats (requires docling)
    "docx", "pptx", "xlsx",
    # Image formats (requires docling for OCR)
    "png", "jpg", "jpeg", "tiff", "tif",
]

VALID_FILE_TYPES = {
    "pdf", "epub", "md", "txt", "rst", "html", "htm",
    "docx", "pptx", "xlsx", "png", "jpg", "jpeg", "tiff", "tif",
}


@dataclass
class Book:
    """Represents an uploaded book."""

    id: UUID
    title: str
    file_path: Path
    file_type: FileType
    created_at: datetime
    author: str | None = None
    chunk_count: int = 0

    def __post_init__(self) -> None:
        if self.file_type not in VALID_FILE_TYPES:
            raise ValueError(
                f"Invalid file_type: {self.file_type}. Must be one of: {VALID_FILE_TYPES}"
            )
