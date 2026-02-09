"""Text chunking for embedding."""

import re
from typing import Any
from uuid import uuid4


class TextChunker:
    """Splits text into overlapping chunks for embedding, with code-aware splitting."""

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        parent_chunk_size: int = 1500,
        children_per_parent: int = 3,
    ):
        """
        Args:
            chunk_size: Target size of each child chunk in characters.
            overlap: Number of characters to overlap between chunks.
            parent_chunk_size: Target size of parent chunks for context (3-4x child size).
            children_per_parent: Number of child chunks to group into one parent.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.parent_chunk_size = parent_chunk_size
        self.children_per_parent = children_per_parent

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
        for match in re.finditer(r"\.\. code-block::\s*(\w*)\n\n((?:    .*\n?)+)", text, re.DOTALL):
            lang = match.group(1) or None
            code_blocks.append((match.start(), match.end(), lang))

        return sorted(code_blocks, key=lambda x: x[0])

    def _is_inside_code_block(
        self, pos: int, code_blocks: list[tuple[int, int, str | None]]
    ) -> bool:
        """Check if position is inside a code block."""
        return any(start <= pos < end for start, end, _ in code_blocks)

    def chunk(self, text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
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
                    block_start < end and block_end > start
                    for block_start, block_end, _ in code_blocks
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

    def chunk_hierarchical(self, text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Create hierarchical chunks with parent context.

        Creates child chunks for retrieval and groups them into parent chunks
        for providing broader context to the LLM.

        Args:
            text: Text to chunk.
            metadata: Metadata to attach to each chunk.

        Returns:
            List of child chunks with parent context attached.
        """
        # First create regular child chunks
        child_chunks = self.chunk(text, metadata)

        if not child_chunks:
            return []

        hierarchical_chunks = []

        # Group child chunks into parents
        for i, child in enumerate(child_chunks):
            # Calculate parent group this child belongs to
            parent_index = i // self.children_per_parent
            parent_start = parent_index * self.children_per_parent
            parent_end = min(parent_start + self.children_per_parent, len(child_chunks))

            # Combine chunks for parent content
            parent_texts = [child_chunks[j]["text"] for j in range(parent_start, parent_end)]
            parent_content = "\n\n".join(parent_texts)

            # Create parent chunk ID (same for all children in this parent group)
            parent_id = uuid4()

            # Add hierarchical metadata
            chunk_with_hierarchy = child.copy()
            chunk_with_hierarchy["metadata"]["sequence_number"] = i
            chunk_with_hierarchy["metadata"]["parent_chunk_id"] = str(parent_id)
            chunk_with_hierarchy["metadata"]["parent_content"] = parent_content

            hierarchical_chunks.append(chunk_with_hierarchy)

        return hierarchical_chunks
