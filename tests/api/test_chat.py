"""Tests for chat endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.domain.exceptions import LLMConnectionError


class TestChatEndpoint:
    def test_chat_returns_answer(self, client: TestClient):
        response = client.post(
            "/api/chat",
            json={"query": "What is the book about?"},
            headers={"session-id": "test-session"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["answer"] == "This is the answer from the LLM."

    def test_chat_includes_sources(self, client: TestClient):
        response = client.post(
            "/api/chat",
            json={"query": "Question?"},
            headers={"session-id": "test-session"},
        )

        data = response.json()
        assert "sources" in data
        assert len(data["sources"]) > 0
        assert "content" in data["sources"][0]
        assert "page_number" in data["sources"][0]

    def test_chat_includes_latency(self, client: TestClient):
        response = client.post(
            "/api/chat",
            json={"query": "Question?"},
            headers={"session-id": "test-session"},
        )

        data = response.json()
        assert "latency_ms" in data
        assert data["latency_ms"] > 0

    def test_chat_requires_session_header(self, client: TestClient):
        response = client.post(
            "/api/chat",
            json={"query": "Question?"},
        )

        assert response.status_code == 422

    def test_chat_requires_query(self, client: TestClient):
        response = client.post(
            "/api/chat",
            json={},
            headers={"session-id": "test-session"},
        )

        assert response.status_code == 422

    def test_chat_handles_llm_error(self, client: TestClient, mock_query_service):
        mock_query_service.query.side_effect = LLMConnectionError("Ollama down")

        response = client.post(
            "/api/chat",
            json={"query": "Question?"},
            headers={"session-id": "test-session"},
        )

        assert response.status_code == 503
        assert "error" in response.json()
