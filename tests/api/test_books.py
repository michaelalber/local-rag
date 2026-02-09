"""Tests for book endpoints."""

from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from src.models import BookNotFoundError, UnsupportedFileTypeError


class TestUploadBooks:
    def test_upload_single_book(self, client: TestClient):
        files = {
            "files": ("test.pdf", BytesIO(b"fake pdf content"), "application/pdf")
        }

        response = client.post(
            "/api/books",
            files=files,
            headers={"session-id": "test-session"},
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Book"

    def test_upload_requires_session_header(self, client: TestClient):
        files = {"files": ("test.pdf", BytesIO(b"content"), "application/pdf")}

        response = client.post("/api/books", files=files)

        assert response.status_code == 422  # Validation error

    def test_upload_rejects_invalid_file_type(
        self, client: TestClient, mock_ingestion_service
    ):
        mock_ingestion_service.ingest_book.side_effect = UnsupportedFileTypeError(
            "Not allowed"
        )

        files = {
            "files": ("test.exe", BytesIO(b"content"), "application/octet-stream")
        }

        response = client.post(
            "/api/books",
            files=files,
            headers={"session-id": "test-session"},
        )

        assert response.status_code == 415


class TestListBooks:
    def test_list_books_returns_books(self, client: TestClient):
        response = client.get(
            "/api/books",
            headers={"session-id": "test-session"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Book"

    def test_list_empty_session(self, client: TestClient, mock_session_manager):
        mock_session_manager.get_books.return_value = []

        response = client.get(
            "/api/books",
            headers={"session-id": "empty-session"},
        )

        assert response.status_code == 200
        assert response.json() == []


class TestDeleteBook:
    def test_delete_book(self, client: TestClient, sample_book):
        response = client.delete(
            f"/api/books/{sample_book.id}",
            headers={"session-id": "test-session"},
        )

        assert response.status_code == 204

    def test_delete_nonexistent_book(self, client: TestClient, mock_session_manager):
        mock_session_manager.remove_book.side_effect = BookNotFoundError("Not found")

        response = client.delete(
            f"/api/books/{uuid4()}",
            headers={"session-id": "test-session"},
        )

        assert response.status_code == 404
