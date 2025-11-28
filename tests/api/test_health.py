"""Tests for health endpoint."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_check_returns_ok(self, client: TestClient):
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_includes_version(self, client: TestClient):
        response = client.get("/api/health")

        data = response.json()
        assert "version" in data
