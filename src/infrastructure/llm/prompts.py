"""RAG prompt construction for LLM queries."""

from src.domain.entities import Chunk


class RAGPromptBuilder:
    """Builds prompts for RAG (Retrieval-Augmented Generation)."""

    def __init__(self, max_context_length: int = 120000):
        """
        Args:
            max_context_length: Maximum characters for context section.
                              Default 120K allows ~80 parent chunks of 1500 chars each.
        """
        self.max_context_length = max_context_length

    def build_prompt(
        self, query: str, context_chunks: list[Chunk], conversation_history: list[dict[str, str]] | None = None
    ) -> str:
        """
        Build a RAG prompt with query and context.

        Args:
            query: User's question.
            context_chunks: Relevant chunks retrieved from vector store.
            conversation_history: Previous messages in the conversation (optional).

        Returns:
            Formatted prompt for LLM.
        """
        if not context_chunks:
            return self._build_no_context_prompt(query, conversation_history)

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

        # Format conversation history if provided
        history_text = ""
        if conversation_history:
            history_parts = []
            for msg in conversation_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_parts.append(f"{role}: {msg['content']}")
            history_text = "\n\nPrevious conversation:\n" + "\n".join(history_parts) + "\n"

        # Build the complete prompt
        prompt = f"""You are a helpful assistant that answers questions STRICTLY based on the provided context from uploaded books.

Context from relevant book sections:
{context_text}{history_text}

User Question: {query}

CRITICAL INSTRUCTIONS - READ CAREFULLY:
- Answer EXCLUSIVELY using information from the context sections above
- DO NOT use your general knowledge, training data, or any external information
- DO NOT mention books, authors, or sources that are not explicitly present in the context above
- If the context does not contain information to answer the question, you MUST respond with:
  "I cannot find information about [topic] in the uploaded book. The available context does not cover this topic."
- Prioritize specific, detailed evidence from the context over general summaries or introductions
- ALWAYS verify every claim against the context before including it in your answer
- Cite specific sources (page numbers or chapters) that appear in the context
- Never fabricate or infer information that is not explicitly stated in the context
- Use direct quotes for important claims, with page citations from the context
- If multiple context sections contain relevant information, synthesize them comprehensively
- Format your response using Markdown for better readability:
  * Use **bold** for emphasis on key terms and important findings
  * Use bullet lists (- item) or numbered lists (1. item) when presenting multiple points
  * Use > blockquotes for direct quotations from the source material
  * Use code blocks with syntax highlighting (```language) for code examples
  * Use inline code (`code`) for technical terms, function names, or short code snippets

Remember: If the information is not in the context above, DO NOT answer from general knowledge.

Answer:"""

        return prompt

    def _build_no_context_prompt(self, query: str, conversation_history: list[dict[str, str]] | None = None) -> str:
        """
        Build prompt when no relevant context is found.

        Args:
            query: User's question.
            conversation_history: Previous messages in the conversation (optional).

        Returns:
            Prompt indicating no context available.
        """
        # Format conversation history if provided
        history_text = ""
        if conversation_history:
            history_parts = []
            for msg in conversation_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_parts.append(f"{role}: {msg['content']}")
            history_text = "\n\nPrevious conversation:\n" + "\n".join(history_parts) + "\n"

        prompt = f"""You are a helpful assistant answering questions based on provided context from books.

Context: No relevant context found in the uploaded books for this query.{history_text}

User Question: {query}

Instructions:
- Inform the user that you cannot find relevant information in the uploaded books to answer their question
- Suggest they may need to upload additional books or rephrase their query
- Do not provide general knowledge answers; only answer based on uploaded book content
- Format your response using Markdown (use **bold** for emphasis, bullet lists, etc.)

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
