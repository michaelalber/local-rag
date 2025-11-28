"""Book entity."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import UUID


@dataclass
class Book:
    """Represents an uploaded book."""

    id: UUID
    title: str
    file_path: Path
    file_type: Literal["pdf", "epub"]
    created_at: datetime
    author: str | None = None
    chunk_count: int = 0

    def __post_init__(self) -> None:
        if self.file_type not in ("pdf", "epub"):
            raise ValueError(f"Invalid file_type: {self.file_type}. Must be 'pdf' or 'epub'.")
