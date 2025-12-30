"""RAG prompt construction for LLM queries."""

from src.models import Chunk


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
        prompt = f"""You are a knowledgeable assistant helping a user explore and discuss their personal ebook library.

Context from the uploaded book(s):
{context_text}{history_text}

User Question: {query}

Instructions:
- Answer the user's question based on the book content provided above
- Be conversational and helpful - explain concepts clearly
- If the context contains exercises or quiz questions, ignore those and focus on the user's actual question
- Summarize key points when appropriate
- Cite page numbers when referencing specific information
- If the context doesn't fully answer the question, say what you found and suggest the user try rephrasing or adjusting retrieval settings
- Use Markdown formatting for readability (bold for key terms, lists for multiple points, code blocks for technical content)

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

        prompt = f"""You are a knowledgeable assistant helping a user explore their personal ebook library.

Context: No relevant passages were retrieved for this query.{history_text}

User Question: {query}

The search didn't find matching content. Please:
- Let the user know you couldn't find relevant passages
- Suggest they try rephrasing the question or increasing the retrieval percentage
- If this seems like a general question about the book (like "what is this book about"), suggest using a higher retrieval % (5-10%)

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
