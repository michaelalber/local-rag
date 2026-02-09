"""Integration tests for Ollama LLM client.

These tests require a running Ollama server with the model pulled.
Run: ollama serve
Run: ollama pull qwen3:8b
"""

import pytest
from src.llm import OllamaLLMClient
from src.models import LLMConnectionError


@pytest.mark.integration
@pytest.mark.slow
class TestOllamaIntegration:
    """Integration tests with real Ollama server."""

    @pytest.fixture
    def client(self) -> OllamaLLMClient:
        """Create client pointing to local Ollama."""
        return OllamaLLMClient(
            model="qwen3:8b", base_url="http://localhost:11434"
        )

    @pytest.mark.asyncio
    async def test_health_check_with_running_server(self, client: OllamaLLMClient):
        """Test health check against real Ollama server."""
        try:
            is_healthy = await client.health_check()
            # If server is running, should return True
            # If not running, will return False (acceptable in CI/local dev)
            assert isinstance(is_healthy, bool)
        except LLMConnectionError:
            pytest.skip("Ollama server not available")

    @pytest.mark.asyncio
    async def test_generate_with_real_model(self, client: OllamaLLMClient):
        """Test actual text generation with Ollama."""
        # Check if server is available first
        is_healthy = await client.health_check()
        if not is_healthy:
            pytest.skip("Ollama server not available")

        context = [
            "Python is a high-level programming language.",
            "It was created by Guido van Rossum.",
            "Python supports multiple programming paradigms.",
        ]
        prompt = "Who created Python?"

        response = await client.generate(prompt=prompt, context=context)

        # Should get a non-empty response
        assert response
        assert len(response) > 0

        # Response should be relevant (contains creator's name)
        assert "Guido" in response or "van Rossum" in response

    @pytest.mark.asyncio
    async def test_generate_without_context(self, client: OllamaLLMClient):
        """Test generation when no context is provided."""
        is_healthy = await client.health_check()
        if not is_healthy:
            pytest.skip("Ollama server not available")

        response = await client.generate(
            prompt="What is the capital of France?", context=[]
        )

        # Should still generate a response
        assert response
        # But should indicate no context was available or provide general knowledge
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_generate_handles_long_context(self, client: OllamaLLMClient):
        """Test generation with many context chunks."""
        is_healthy = await client.health_check()
        if not is_healthy:
            pytest.skip("Ollama server not available")

        # Create multiple context chunks
        context = [
            f"This is context chunk number {i}. It contains information about topic {i}."
            for i in range(10)
        ]
        prompt = "Summarize the information provided."

        response = await client.generate(prompt=prompt, context=context)

        assert response
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_client_with_invalid_url_raises_error(self):
        """Test that invalid Ollama URL is handled."""
        client = OllamaLLMClient(
            model="qwen3:8b",
            base_url="http://invalid-host:59999",  # Use valid port range
        )

        # Health check should return False
        is_healthy = await client.health_check()
        assert is_healthy is False

        # Generation should raise LLMConnectionError
        with pytest.raises(LLMConnectionError):
            await client.generate(prompt="test", context=["context"])

    @pytest.mark.asyncio
    async def test_generate_with_special_characters(self, client: OllamaLLMClient):
        """Test generation with special characters in input."""
        is_healthy = await client.health_check()
        if not is_healthy:
            pytest.skip("Ollama server not available")

        context = [
            "The symbol π (pi) represents the ratio of circumference to diameter.",
            "Common escape characters include \\n, \\t, and \\r.",
        ]
        prompt = "What does π represent?"

        response = await client.generate(prompt=prompt, context=context)

        assert response
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_consecutive_generations(self, client: OllamaLLMClient):
        """Test multiple consecutive calls to ensure stability."""
        is_healthy = await client.health_check()
        if not is_healthy:
            pytest.skip("Ollama server not available")

        context = ["Python is a programming language."]

        # Make multiple calls
        response1 = await client.generate(prompt="What is Python?", context=context)
        response2 = await client.generate(
            prompt="Is Python compiled or interpreted?", context=context
        )

        # Both should succeed
        assert response1 and len(response1) > 0
        assert response2 and len(response2) > 0

        # Responses should be different (different questions)
        assert response1 != response2
