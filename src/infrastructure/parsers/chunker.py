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
                chunks.append({"text": chunk_text, "metadata": metadata.copy()})

            # Move start position, accounting for overlap
            start = end - self.overlap if end < len(text) else end

        return chunks
