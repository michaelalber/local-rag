"""Ollama LLM client implementation."""

import logging
from collections.abc import AsyncGenerator

import ollama

from src.models import Chunk, LLMConnectionError

from .prompts import RAGPromptBuilder

logger = logging.getLogger(__name__)


class OllamaLLMClient:
    """LLM client using Ollama for local inference."""

    def __init__(
        self, model: str = "qwen3:14b", base_url: str = "http://localhost:11434"
    ):
        """
        Args:
            model: Ollama model name.
            base_url: Ollama server URL.
        """
        self.model = model
        self.client = ollama.AsyncClient(host=base_url)
        self.prompt_builder = RAGPromptBuilder()

    async def generate(
        self,
        prompt: str,
        context: list[str] | list[Chunk],
        conversation_history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> str:
        """
        Generate response using Ollama with RAG context.

        Args:
            prompt: User's question.
            context: List of relevant text chunks (strings or Chunk objects).
            conversation_history: Previous messages in the conversation (optional).
            model: Override default model for this request (optional).

        Returns:
            Generated response.

        Raises:
            LLMConnectionError: If Ollama server is unreachable or returns error.
        """
        try:
            # Handle both string context and Chunk objects
            if context and isinstance(context[0], str):
                # Convert context strings to minimal Chunk objects
                chunks = [
                    Chunk(
                        id=None,
                        book_id=None,
                        content=text,
                    )
                    for text in context
                ]
            else:
                # Already Chunk objects with metadata
                chunks = context

            # Build the RAG prompt
            full_prompt = self.prompt_builder.build_prompt(
                query=prompt, context_chunks=chunks, conversation_history=conversation_history
            )

            # Use provided model or default
            selected_model = model if model else self.model

            # Call Ollama chat endpoint
            response = await self.client.chat(
                model=selected_model,
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
            logger.error("Ollama API error: %s", e)
            raise LLMConnectionError(f"Ollama API error: {e}") from e
        except (ConnectionError, TimeoutError, OSError) as e:
            logger.error("Failed to connect to Ollama server: %s", e)
            raise LLMConnectionError(f"Failed to connect to Ollama server: {e}") from e
        except LLMConnectionError:
            raise
        except Exception as e:
            logger.error("Unexpected error during LLM generation: %s", e)
            raise LLMConnectionError(f"Unexpected error: {e}") from e

    async def generate_stream(
        self,
        prompt: str,
        context: list[str] | list[Chunk],
        conversation_history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response using Ollama with RAG context.

        Yields tokens as they are generated for real-time streaming.

        Args:
            prompt: User's question.
            context: List of relevant text chunks (strings or Chunk objects).
            conversation_history: Previous messages in the conversation (optional).
            model: Override default model for this request (optional).

        Yields:
            Individual response tokens as they arrive.

        Raises:
            LLMConnectionError: If Ollama server is unreachable or returns error.
        """
        try:
            # Handle both string context and Chunk objects
            if context and isinstance(context[0], str):
                chunks = [
                    Chunk(id=None, book_id=None, content=text)
                    for text in context
                ]
            else:
                chunks = context

            # Build the RAG prompt
            full_prompt = self.prompt_builder.build_prompt(
                query=prompt, context_chunks=chunks, conversation_history=conversation_history
            )

            # Use provided model or default
            selected_model = model if model else self.model

            # Stream response from Ollama
            async for chunk in await self.client.chat(
                model=selected_model,
                messages=[{"role": "user", "content": full_prompt}],
                stream=True,
            ):
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]

        except ollama.ResponseError as e:
            logger.error("Ollama API error during streaming: %s", e)
            raise LLMConnectionError(f"Ollama API error: {e}") from e
        except (ConnectionError, TimeoutError, OSError) as e:
            logger.error("Failed to connect to Ollama server: %s", e)
            raise LLMConnectionError(f"Failed to connect to Ollama server: {e}") from e
        except LLMConnectionError:
            raise
        except Exception as e:
            logger.error("Unexpected error during LLM streaming: %s", e)
            raise LLMConnectionError(f"Unexpected error: {e}") from e

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
