"""Tests for session manager."""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.services import SessionManager
from src.models import Book, BookNotFoundError, SessionLimitError


class TestSessionManager:
    @pytest.fixture
    def manager(self) -> SessionManager:
        return SessionManager(max_books=3)

    @pytest.fixture
    def sample_book(self) -> Book:
        return Book(
            id=uuid4(),
            title="Test Book",
            author="Test Author",
            file_path=Path("/uploads/test.pdf"),
            file_type="pdf",
            created_at=datetime.now(timezone.utc),
        )

    def test_add_book_to_session(self, manager: SessionManager, sample_book: Book):
        session_id = "session-1"
        manager.add_book(session_id, sample_book)

        books = manager.get_books(session_id)
        assert len(books) == 1
        assert books[0].id == sample_book.id

    def test_get_books_empty_session(self, manager: SessionManager):
        books = manager.get_books("nonexistent")
        assert books == []

    def test_session_limit_enforced(self, manager: SessionManager):
        session_id = "limited-session"

        # Add max books
        for i in range(3):
            book = Book(
                id=uuid4(),
                title=f"Book {i}",
                author=None,
                file_path=Path(f"/uploads/book{i}.pdf"),
                file_type="pdf",
                created_at=datetime.now(timezone.utc),
            )
            manager.add_book(session_id, book)

        # Fourth should fail
        extra_book = Book(
            id=uuid4(),
            title="Extra Book",
            author=None,
            file_path=Path("/uploads/extra.pdf"),
            file_type="pdf",
            created_at=datetime.now(timezone.utc),
        )

        with pytest.raises(SessionLimitError):
            manager.add_book(session_id, extra_book)

    def test_remove_book(self, manager: SessionManager, sample_book: Book):
        session_id = "session-1"
        manager.add_book(session_id, sample_book)

        manager.remove_book(session_id, sample_book.id)

        assert manager.get_books(session_id) == []

    def test_remove_nonexistent_book(self, manager: SessionManager):
        with pytest.raises(BookNotFoundError):
            manager.remove_book("session-1", uuid4())

    def test_clear_session(self, manager: SessionManager, sample_book: Book):
        session_id = "session-1"
        manager.add_book(session_id, sample_book)

        manager.clear_session(session_id)

        assert manager.get_books(session_id) == []

    def test_sessions_are_isolated(self, manager: SessionManager):
        book1 = Book(
            id=uuid4(),
            title="Book 1",
            author=None,
            file_path=Path("/b1.pdf"),
            file_type="pdf",
            created_at=datetime.now(timezone.utc),
        )
        book2 = Book(
            id=uuid4(),
            title="Book 2",
            author=None,
            file_path=Path("/b2.pdf"),
            file_type="pdf",
            created_at=datetime.now(timezone.utc),
        )

        manager.add_book("session-a", book1)
        manager.add_book("session-b", book2)

        assert len(manager.get_books("session-a")) == 1
        assert manager.get_books("session-a")[0].title == "Book 1"
        assert len(manager.get_books("session-b")) == 1
        assert manager.get_books("session-b")[0].title == "Book 2"
