"""Document parser interface."""

from abc import ABC, abstractmethod
from pathlib import Path


class DocumentParser(ABC):
    """Interface for parsing documents into chunks."""

    @abstractmethod
    def parse(self, file_path: Path) -> tuple[str, str | None]:
        """
        Parse document and extract metadata.

        Returns:
            Tuple of (title, author). Author may be None.
        """
        pass

    @abstractmethod
    def extract_text(self, file_path: Path) -> list[tuple[str, dict]]:
        """
        Extract text with metadata.

        Returns:
            List of (text, metadata) tuples. Metadata contains page_number or chapter.
        """
        pass
