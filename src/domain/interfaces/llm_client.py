"""LLM client interface."""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Interface for LLM interactions."""

    @abstractmethod
    async def generate(self, prompt: str, context: list[str]) -> str:
        """
        Generate response using context.

        Args:
            prompt: User question.
            context: Relevant text chunks for RAG.

        Returns:
            Generated response.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if LLM service is available."""
        pass
