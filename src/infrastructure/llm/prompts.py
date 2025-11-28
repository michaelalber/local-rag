"""RAG prompt construction for LLM queries."""

from src.domain.entities import Chunk


class RAGPromptBuilder:
    """Builds prompts for RAG (Retrieval-Augmented Generation)."""

    def __init__(self, max_context_length: int = 6000):
        """
        Args:
            max_context_length: Maximum characters for context section.
        """
        self.max_context_length = max_context_length

    def build_prompt(self, query: str, context_chunks: list[Chunk]) -> str:
        """
        Build a RAG prompt with query and context.

        Args:
            query: User's question.
            context_chunks: Relevant chunks retrieved from vector store.

        Returns:
            Formatted prompt for LLM.
        """
        if not context_chunks:
            return self._build_no_context_prompt(query)

        # Format context with source attribution
        context_parts = []
        total_length = 0

        for chunk in context_chunks:
            # Build source attribution
            source_info = self._format_source(chunk)
            chunk_text = f"{chunk.content}\n[Source: {source_info}]"

            # Check length limit
            if total_length + len(chunk_text) > self.max_context_length:
                break

            context_parts.append(chunk_text)
            total_length += len(chunk_text)

        context_text = "\n\n".join(context_parts)

        # Build the complete prompt
        prompt = f"""You are a helpful assistant answering questions based on provided context from books.

Context from relevant book sections:
{context_text}

User Question: {query}

Instructions:
- Answer the question using only the information provided in the context above
- Cite specific sources when making claims (reference page numbers or chapters)
- If the context doesn't contain enough information to fully answer the question, acknowledge this
- Be concise and accurate
- Use direct quotes when appropriate

Answer:"""

        return prompt

    def _build_no_context_prompt(self, query: str) -> str:
        """
        Build prompt when no relevant context is found.

        Args:
            query: User's question.

        Returns:
            Prompt indicating no context available.
        """
        prompt = f"""You are a helpful assistant answering questions based on provided context from books.

Context: No relevant context found in the uploaded books for this query.

User Question: {query}

Instructions:
- Inform the user that you cannot find relevant information in the uploaded books to answer their question
- Suggest they may need to upload additional books or rephrase their query
- Do not provide general knowledge answers; only answer based on uploaded book content

Answer:"""

        return prompt

    def _format_source(self, chunk: Chunk) -> str:
        """
        Format source attribution for a chunk.

        Args:
            chunk: Chunk to format source for.

        Returns:
            Formatted source string.
        """
        parts = []

        if chunk.chapter:
            parts.append(f"Chapter: {chunk.chapter}")

        if chunk.page_number is not None:
            parts.append(f"Page {chunk.page_number}")

        if not parts:
            # Fallback if no metadata
            parts.append("Book content")

        return ", ".join(parts)
