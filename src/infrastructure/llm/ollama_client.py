"""Ollama LLM client implementation."""

import ollama

from src.domain.entities import Chunk
from src.domain.exceptions import LLMConnectionError
from src.domain.interfaces import LLMClient
from src.infrastructure.llm.prompts import RAGPromptBuilder


class OllamaLLMClient(LLMClient):
    """LLM client using Ollama for local inference."""

    def __init__(
        self, model: str = "mistral:7b-instruct-q4_K_M", base_url: str = "http://localhost:11434"
    ):
        """
        Args:
            model: Ollama model name.
            base_url: Ollama server URL.
        """
        self.model = model
        self.client = ollama.AsyncClient(host=base_url)
        self.prompt_builder = RAGPromptBuilder()

    async def generate(self, prompt: str, context: list[str]) -> str:
        """
        Generate response using Ollama with RAG context.

        Args:
            prompt: User's question.
            context: List of relevant text chunks.

        Returns:
            Generated response.

        Raises:
            LLMConnectionError: If Ollama server is unreachable or returns error.
        """
        try:
            # Convert context strings to Chunk objects for prompt builder
            # Note: In real usage, these would be Chunk entities with metadata
            # For now, create minimal chunks from context strings
            chunks = [
                Chunk(
                    id=None,  # Not needed for prompt building
                    book_id=None,  # Not needed for prompt building
                    content=text,
                )
                for text in context
            ]

            # Build the RAG prompt
            full_prompt = self.prompt_builder.build_prompt(
                query=prompt, context_chunks=chunks
            )

            # Call Ollama chat endpoint
            response = await self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": full_prompt}],
                stream=False,
            )

            # Extract response text
            if "message" not in response or "content" not in response["message"]:
                raise LLMConnectionError(
                    f"Malformed response from Ollama: {response}"
                )

            return response["message"]["content"]

        except ollama.ResponseError as e:
            raise LLMConnectionError(f"Ollama API error: {e}") from e
        except Exception as e:
            if isinstance(e, LLMConnectionError):
                raise
            raise LLMConnectionError(
                f"Failed to connect to Ollama server: {e}"
            ) from e

    async def health_check(self) -> bool:
        """
        Check if Ollama server is available.

        Returns:
            True if server is reachable, False otherwise.
        """
        try:
            # Try to list models to verify server is responding
            await self.client.list()
            return True
        except Exception:
            return False
