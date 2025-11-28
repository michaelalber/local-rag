# Phase 4: LLM Integration

## Objective

Implement Ollama client for local LLM inference with RAG prompt construction.

## Files to Create

```
src/infrastructure/llm/
├── __init__.py
├── ollama_client.py
└── prompts.py
tests/unit/infrastructure/llm/
├── __init__.py
├── test_ollama_client.py
└── test_prompts.py
tests/integration/
└── test_ollama_integration.py
```

## Prerequisites

Ensure Ollama is installed and model is pulled:

```bash
# Start Ollama (if not running)
ollama serve

# Pull the model (one-time)
ollama pull mistral:7b-instruct-q4_K_M

# Verify
ollama list
```

## Write Tests First

### tests/unit/infrastructure/llm/test_prompts.py

```python
"""Tests for RAG prompt construction."""

import pytest

from src.infrastructure.llm.prompts import RAGPromptBuilder


class TestRAGPromptBuilder:
    @pytest.fixture
    def builder(self) -> RAGPromptBuilder:
        return RAGPromptBuilder()

    def test_build_prompt_includes_context(self, builder: RAGPromptBuilder):
        context = ["First chunk of text.", "Second chunk of text."]
        question = "What is discussed?"
        
        prompt = builder.build(question=question, context=context)
        
        assert "First chunk of text" in prompt
        assert "Second chunk of text" in prompt
        assert question in prompt

    def test_build_prompt_with_empty_context(self, builder: RAGPromptBuilder):
        prompt = builder.build(question="What is this?", context=[])
        
        assert "What is this?" in prompt
        # Should still produce valid prompt
        assert len(prompt) > 0

    def test_build_prompt_has_structure(self, builder: RAGPromptBuilder):
        prompt = builder.build(
            question="Tell me about X",
            context=["Context about X here."]
        )
        
        # Should have clear sections
        assert "Context" in prompt or "context" in prompt
        assert "Question" in prompt or "question" in prompt or "Tell me about X" in prompt

    def test_build_prompt_instructs_to_use_context(self, builder: RAGPromptBuilder):
        prompt = builder.build(question="Q?", context=["Info"])
        
        # Should instruct the model to base answer on context
        prompt_lower = prompt.lower()
        assert any(word in prompt_lower for word in ["context", "provided", "based on", "above"])

    def test_truncates_long_context(self, builder: RAGPromptBuilder):
        # Very long context chunks
        long_context = ["x" * 10000 for _ in range(10)]
        prompt = builder.build(question="Q?", context=long_context, max_context_chars=5000)
        
        # Should be truncated
        assert len(prompt) < 100000  # Reasonable limit
```

### tests/unit/infrastructure/llm/test_ollama_client.py

```python
"""Tests for Ollama client (unit tests with mocking)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.infrastructure.llm.ollama_client import OllamaLLMClient
from src.domain.exceptions import LLMConnectionError


class TestOllamaLLMClient:
    @pytest.fixture
    def mock_ollama(self):
        with patch("src.infrastructure.llm.ollama_client.AsyncClient") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_ollama) -> OllamaLLMClient:
        return OllamaLLMClient(model="mistral:7b-instruct-q4_K_M")

    @pytest.mark.asyncio
    async def test_generate_returns_response(self, client: OllamaLLMClient, mock_ollama):
        # Setup mock
        mock_instance = mock_ollama.return_value
        mock_instance.generate = AsyncMock(return_value={
            "response": "This is the generated answer."
        })
        
        result = await client.generate(
            prompt="What is Python?",
            context=["Python is a programming language."]
        )
        
        assert result == "This is the generated answer."
        mock_instance.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_builds_rag_prompt(self, client: OllamaLLMClient, mock_ollama):
        mock_instance = mock_ollama.return_value
        mock_instance.generate = AsyncMock(return_value={"response": "Answer"})
        
        await client.generate(
            prompt="Question?",
            context=["Context chunk 1", "Context chunk 2"]
        )
        
        # Check that the call included context
        call_args = mock_instance.generate.call_args
        prompt_sent = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        
        # The prompt should contain our context
        assert "Context chunk 1" in prompt_sent or "context" in str(call_args).lower()

    @pytest.mark.asyncio
    async def test_health_check_success(self, client: OllamaLLMClient, mock_ollama):
        mock_instance = mock_ollama.return_value
        mock_instance.list = AsyncMock(return_value={"models": []})
        
        result = await client.health_check()
        
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, client: OllamaLLMClient, mock_ollama):
        mock_instance = mock_ollama.return_value
        mock_instance.list = AsyncMock(side_effect=Exception("Connection refused"))
        
        result = await client.health_check()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_generate_handles_connection_error(self, client: OllamaLLMClient, mock_ollama):
        mock_instance = mock_ollama.return_value
        mock_instance.generate = AsyncMock(side_effect=Exception("Connection refused"))
        
        with pytest.raises(LLMConnectionError):
            await client.generate(prompt="Test", context=[])
```

### tests/integration/test_ollama_integration.py

```python
"""Integration tests for Ollama (requires running Ollama server)."""

import pytest

from src.infrastructure.llm import OllamaLLMClient


@pytest.mark.integration
@pytest.mark.slow
class TestOllamaIntegration:
    """
    These tests require a running Ollama server with the model pulled.
    
    Run with: pytest tests/integration/test_ollama_integration.py -v -m integration
    Skip with: pytest -m "not integration"
    """

    @pytest.fixture
    def client(self) -> OllamaLLMClient:
        return OllamaLLMClient(model="mistral:7b-instruct-q4_K_M")

    @pytest.mark.asyncio
    async def test_health_check_with_real_server(self, client: OllamaLLMClient):
        result = await client.health_check()
        
        if not result:
            pytest.skip("Ollama server not running")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_generate_with_real_model(self, client: OllamaLLMClient):
        # First check if server is available
        if not await client.health_check():
            pytest.skip("Ollama server not running")
        
        response = await client.generate(
            prompt="What is 2 + 2? Answer with just the number.",
            context=[]
        )
        
        assert response is not None
        assert len(response) > 0
        assert "4" in response

    @pytest.mark.asyncio
    async def test_rag_generation(self, client: OllamaLLMClient):
        if not await client.health_check():
            pytest.skip("Ollama server not running")
        
        context = [
            "The LocalBookChat application allows users to chat with their eBooks.",
            "It uses ChromaDB for vector storage and Ollama for local LLM inference.",
            "Users can upload up to 5 books per session.",
        ]
        
        response = await client.generate(
            prompt="How many books can a user upload?",
            context=context
        )
        
        assert "5" in response or "five" in response.lower()
```

## Implementation

### src/infrastructure/llm/prompts.py

```python
"""RAG prompt templates and builders."""


class RAGPromptBuilder:
    """Builds prompts for RAG-based question answering."""

    DEFAULT_TEMPLATE = """Answer the question based on the provided context. If the context doesn't contain enough information to fully answer the question, say so and provide what information you can.

Be concise and direct in your response.

Context:
{context}

Question: {question}

Answer:"""

    def __init__(self, template: str | None = None):
        """
        Args:
            template: Custom prompt template. Must contain {context} and {question}.
        """
        self.template = template or self.DEFAULT_TEMPLATE

    def build(
        self,
        question: str,
        context: list[str],
        max_context_chars: int = 8000,
    ) -> str:
        """
        Build a RAG prompt.

        Args:
            question: User's question.
            context: List of relevant text chunks.
            max_context_chars: Maximum characters for context section.

        Returns:
            Formatted prompt string.
        """
        # Join and potentially truncate context
        context_text = self._format_context(context, max_context_chars)
        
        return self.template.format(
            context=context_text,
            question=question,
        )

    def _format_context(self, chunks: list[str], max_chars: int) -> str:
        """Format context chunks with truncation if needed."""
        if not chunks:
            return "No context available."

        formatted_chunks = []
        total_chars = 0

        for i, chunk in enumerate(chunks, 1):
            # Format each chunk with a number
            formatted = f"[{i}] {chunk.strip()}"
            
            if total_chars + len(formatted) > max_chars:
                # Truncate this chunk to fit
                remaining = max_chars - total_chars - 50  # Leave room for truncation notice
                if remaining > 100:
                    formatted = formatted[:remaining] + "... [truncated]"
                    formatted_chunks.append(formatted)
                break
            
            formatted_chunks.append(formatted)
            total_chars += len(formatted) + 2  # +2 for newlines

        return "\n\n".join(formatted_chunks)
```

### src/infrastructure/llm/ollama_client.py

```python
"""Ollama LLM client implementation."""

from ollama import AsyncClient

from src.domain.interfaces import LLMClient
from src.domain.exceptions import LLMConnectionError
from .prompts import RAGPromptBuilder


class OllamaLLMClient(LLMClient):
    """LLM client using local Ollama server."""

    def __init__(
        self,
        model: str = "mistral:7b-instruct-q4_K_M",
        base_url: str = "http://localhost:11434",
        prompt_builder: RAGPromptBuilder | None = None,
    ):
        """
        Args:
            model: Ollama model name.
            base_url: Ollama server URL.
            prompt_builder: Custom prompt builder (optional).
        """
        self.model = model
        self.client = AsyncClient(host=base_url)
        self.prompt_builder = prompt_builder or RAGPromptBuilder()

    async def generate(self, prompt: str, context: list[str]) -> str:
        """
        Generate response using RAG context.

        Args:
            prompt: User's question.
            context: Relevant text chunks.

        Returns:
            Generated response.

        Raises:
            LLMConnectionError: If Ollama server is unreachable.
        """
        full_prompt = self.prompt_builder.build(question=prompt, context=context)
        
        try:
            response = await self.client.generate(
                model=self.model,
                prompt=full_prompt,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 1024,  # Max tokens to generate
                },
            )
            return response["response"]
        
        except Exception as e:
            raise LLMConnectionError(f"Failed to connect to Ollama: {e}") from e

    async def health_check(self) -> bool:
        """Check if Ollama server is available."""
        try:
            await self.client.list()
            return True
        except Exception:
            return False
```

### src/infrastructure/llm/__init__.py

```python
"""LLM infrastructure."""

from .ollama_client import OllamaLLMClient
from .prompts import RAGPromptBuilder

__all__ = ["OllamaLLMClient", "RAGPromptBuilder"]
```

## Update pytest.ini for markers

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
markers = [
    "integration: marks tests as integration tests (may require external services)",
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
```

## Verification

```bash
# Run unit tests (no Ollama required)
pytest tests/unit/infrastructure/llm/ -v

# Run integration tests (requires Ollama running)
ollama serve  # In another terminal
pytest tests/integration/test_ollama_integration.py -v -m integration

# Skip slow/integration tests for quick feedback
pytest -m "not integration and not slow"

# Manual test
python -c "
import asyncio
from src.infrastructure.llm import OllamaLLMClient

async def test():
    client = OllamaLLMClient()
    
    if not await client.health_check():
        print('Ollama not running!')
        return
    
    response = await client.generate(
        prompt='What is the capital of France?',
        context=['France is a country in Western Europe. Paris is its capital and largest city.']
    )
    print(f'Response: {response}')

asyncio.run(test())
"
```

## Commit

```bash
git add .
git commit -m "feat: implement Ollama LLM client with RAG prompt builder"
```

## Next Phase

Proceed to `docs/phases/PHASE_5_SERVICES.md`
