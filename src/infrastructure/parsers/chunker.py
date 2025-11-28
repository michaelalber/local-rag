"""Text chunking for embedding."""

import re


class TextChunker:
    """Splits text into overlapping chunks for embedding, with code-aware splitting."""

    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        """
        Args:
            chunk_size: Target size of each chunk in characters.
            overlap: Number of characters to overlap between chunks.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _detect_code_blocks(self, text: str) -> list[tuple[int, int, str | None]]:
        """
        Detect code blocks in text.

        Returns:
            List of (start_pos, end_pos, language) tuples for each code block.
        """
        code_blocks = []

        # Detect markdown-style code blocks: ```language\n...\n```
        for match in re.finditer(r"```(\w*)\n(.*?)\n```", text, re.DOTALL):
            lang = match.group(1) or None
            code_blocks.append((match.start(), match.end(), lang))

        # Detect RST-style code blocks: .. code-block:: language
        for match in re.finditer(
            r"\.\. code-block::\s*(\w*)\n\n((?:    .*\n?)+)", text, re.DOTALL
        ):
            lang = match.group(1) or None
            code_blocks.append((match.start(), match.end(), lang))

        return sorted(code_blocks, key=lambda x: x[0])

    def _is_inside_code_block(self, pos: int, code_blocks: list[tuple[int, int, str | None]]) -> bool:
        """Check if position is inside a code block."""
        for start, end, _ in code_blocks:
            if start <= pos < end:
                return True
        return False

    def chunk(self, text: str, metadata: dict) -> list[dict]:
        """
        Split text into chunks with metadata, preserving code blocks.

        Args:
            text: Text to chunk.
            metadata: Metadata to attach to each chunk.

        Returns:
            List of {"text": str, "metadata": dict} dicts.
        """
        if not text or not text.strip():
            return []

        text = text.strip()

        # Detect code blocks
        code_blocks = self._detect_code_blocks(text)

        # If text fits in one chunk, return as-is
        if len(text) <= self.chunk_size:
            has_code = len(code_blocks) > 0
            chunk_metadata = metadata.copy()
            chunk_metadata["has_code"] = has_code
            if has_code and code_blocks[0][2]:
                chunk_metadata["code_language"] = code_blocks[0][2]
            return [{"text": text, "metadata": chunk_metadata}]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # If not at the end, try to find a good breaking point
            if end < len(text):
                # Check if we're inside a code block
                if self._is_inside_code_block(end, code_blocks):
                    # Try to find the end of the code block
                    for block_start, block_end, _ in code_blocks:
                        if block_start <= end < block_end:
                            # If the whole block fits from start, include it
                            if block_end - start <= self.chunk_size * 1.5:
                                end = block_end
                            else:
                                # Otherwise, end before the code block
                                end = block_start
                            break
                else:
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
                # Determine if this chunk contains code
                has_code = any(
                    block_start < end and block_end > start for block_start, block_end, _ in code_blocks
                )

                chunk_metadata = metadata.copy()
                chunk_metadata["has_code"] = has_code

                # Add language if there's a code block
                if has_code:
                    for block_start, block_end, lang in code_blocks:
                        if block_start < end and block_end > start and lang:
                            chunk_metadata["code_language"] = lang
                            break

                chunks.append({"text": chunk_text, "metadata": chunk_metadata})

            # Move start position, accounting for overlap
            start = end - self.overlap if end < len(text) else end

        return chunks
