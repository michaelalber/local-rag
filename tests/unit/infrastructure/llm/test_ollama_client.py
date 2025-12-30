"""Unit tests for Ollama LLM client with mocks."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models import LLMConnectionError
from src.llm import OllamaLLMClient


class TestOllamaLLMClient:
    """Test Ollama client with mocked ollama library."""

    @pytest.fixture
    def mock_ollama_client(self):
        """Mock ollama.AsyncClient."""
        with patch("src.llm.ollama_client.ollama.AsyncClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def client(self, mock_ollama_client) -> OllamaLLMClient:
        """Create OllamaLLMClient with mocked dependencies."""
        return OllamaLLMClient(
            model="mistral:7b-instruct-q4_K_M", base_url="http://localhost:11434"
        )

    @pytest.mark.asyncio
    async def test_generate_success(
        self, client: OllamaLLMClient, mock_ollama_client: AsyncMock
    ):
        """Test successful text generation."""
        # Mock the chat response
        mock_response = {
            "message": {"content": "Python is a programming language."},
            "done": True,
        }
        mock_ollama_client.chat.return_value = mock_response

        prompt = "What is Python?"
        context = ["Python is a high-level language.", "Python supports OOP."]

        result = await client.generate(prompt=prompt, context=context)

        assert result == "Python is a programming language."
        mock_ollama_client.chat.assert_called_once()

        # Verify the call structure
        call_args = mock_ollama_client.chat.call_args
        assert call_args.kwargs["model"] == "mistral:7b-instruct-q4_K_M"
        assert "messages" in call_args.kwargs
        assert len(call_args.kwargs["messages"]) > 0

    @pytest.mark.asyncio
    async def test_generate_with_empty_context(
        self, client: OllamaLLMClient, mock_ollama_client: AsyncMock
    ):
        """Test generation with no context."""
        mock_response = {
            "message": {"content": "I cannot find information about that."},
            "done": True,
        }
        mock_ollama_client.chat.return_value = mock_response

        result = await client.generate(prompt="What is this?", context=[])

        assert "cannot find" in result.lower()
        mock_ollama_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_connection_error(
        self, client: OllamaLLMClient, mock_ollama_client: AsyncMock
    ):
        """Test handling of connection errors."""
        # Simulate connection failure
        mock_ollama_client.chat.side_effect = Exception("Connection refused")

        with pytest.raises(LLMConnectionError) as exc_info:
            await client.generate(prompt="test", context=["context"])

        assert "connection" in str(exc_info.value).lower() or "ollama" in str(
            exc_info.value
        ).lower()

    @pytest.mark.asyncio
    async def test_health_check_success(
        self, client: OllamaLLMClient, mock_ollama_client: AsyncMock
    ):
        """Test successful health check."""
        # Mock the list response to indicate server is available
        mock_ollama_client.list.return_value = {
            "models": [{"name": "mistral:7b-instruct-q4_K_M"}]
        }

        is_healthy = await client.health_check()

        assert is_healthy is True
        mock_ollama_client.list.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_server_unreachable(
        self, client: OllamaLLMClient, mock_ollama_client: AsyncMock
    ):
        """Test health check when server is unreachable."""
        mock_ollama_client.list.side_effect = Exception("Connection refused")

        is_healthy = await client.health_check()

        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_generate_uses_prompt_builder(
        self, client: OllamaLLMClient, mock_ollama_client: AsyncMock
    ):
        """Test that generation integrates with prompt builder."""
        mock_response = {"message": {"content": "Response text"}, "done": True}
        mock_ollama_client.chat.return_value = mock_response

        await client.generate(prompt="Query", context=["Chunk 1", "Chunk 2"])

        # Verify that messages were constructed
        call_args = mock_ollama_client.chat.call_args
        messages = call_args.kwargs["messages"]

        # Should have at least a user message
        assert any(msg["role"] == "user" for msg in messages)

        # User message should contain the query
        user_message = next(msg for msg in messages if msg["role"] == "user")
        assert "Query" in user_message["content"]

    @pytest.mark.asyncio
    async def test_generate_handles_streaming_disabled(
        self, client: OllamaLLMClient, mock_ollama_client: AsyncMock
    ):
        """Test that client uses non-streaming mode."""
        mock_response = {"message": {"content": "Test response"}, "done": True}
        mock_ollama_client.chat.return_value = mock_response

        await client.generate(prompt="test", context=["context"])

        call_args = mock_ollama_client.chat.call_args
        # Should not enable streaming
        assert call_args.kwargs.get("stream", False) is False

    @pytest.mark.asyncio
    async def test_client_initialization_with_custom_url(
        self, mock_ollama_client: AsyncMock
    ):
        """Test client can be initialized with custom base URL."""
        client = OllamaLLMClient(
            model="llama2:7b", base_url="http://custom-host:8080"
        )

        # The client should be created (no exception)
        assert client is not None

    @pytest.mark.asyncio
    async def test_generate_with_malformed_response(
        self, client: OllamaLLMClient, mock_ollama_client: AsyncMock
    ):
        """Test handling of malformed API responses."""
        # Response missing expected structure
        mock_ollama_client.chat.return_value = {"invalid": "structure"}

        with pytest.raises((LLMConnectionError, KeyError)):
            await client.generate(prompt="test", context=["context"])

    @pytest.mark.asyncio
    async def test_generate_preserves_context_order(
        self, client: OllamaLLMClient, mock_ollama_client: AsyncMock
    ):
        """Test that context chunks are used in order."""
        mock_response = {"message": {"content": "Answer"}, "done": True}
        mock_ollama_client.chat.return_value = mock_response

        context = ["First chunk", "Second chunk", "Third chunk"]
        await client.generate(prompt="Query", context=context)

        call_args = mock_ollama_client.chat.call_args
        messages = call_args.kwargs["messages"]
        user_message = next(msg for msg in messages if msg["role"] == "user")

        # Context should appear in order in the prompt
        content = user_message["content"]
        idx_first = content.find("First chunk")
        idx_second = content.find("Second chunk")
        idx_third = content.find("Third chunk")

        assert idx_first < idx_second < idx_third
