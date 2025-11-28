"""LLM client interface."""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Interface for LLM interactions."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: list[str],
        conversation_history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> str:
        """
        Generate response using context.

        Args:
            prompt: User question.
            context: Relevant text chunks for RAG.
            conversation_history: Previous messages in the conversation (optional).
            model: Override default model for this request (optional).

        Returns:
            Generated response.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if LLM service is available."""
        pass
