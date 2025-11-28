"""Session management for loaded books."""

from uuid import UUID

from src.domain.entities import Book
from src.domain.exceptions import BookNotFoundError, SessionLimitError


class SessionManager:
    """Manages book sessions with limits."""

    def __init__(self, max_books: int = 5):
        """
        Args:
            max_books: Maximum books per session.
        """
        self.max_books = max_books
        self._sessions: dict[str, list[Book]] = {}

    def add_book(self, session_id: str, book: Book) -> None:
        """
        Add a book to a session.

        Raises:
            SessionLimitError: If session is at max capacity.
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        if len(self._sessions[session_id]) >= self.max_books:
            raise SessionLimitError(
                f"Session limit of {self.max_books} books reached. "
                "Remove a book before adding more."
            )

        self._sessions[session_id].append(book)

    def get_books(self, session_id: str) -> list[Book]:
        """Get all books in a session."""
        return self._sessions.get(session_id, []).copy()

    def get_book(self, session_id: str, book_id: UUID) -> Book:
        """
        Get a specific book.

        Raises:
            BookNotFoundError: If book not found.
        """
        books = self._sessions.get(session_id, [])
        for book in books:
            if book.id == book_id:
                return book
        raise BookNotFoundError(f"Book {book_id} not found in session {session_id}")

    def remove_book(self, session_id: str, book_id: UUID) -> None:
        """
        Remove a book from a session.

        Raises:
            BookNotFoundError: If book not found.
        """
        books = self._sessions.get(session_id, [])
        for i, book in enumerate(books):
            if book.id == book_id:
                del books[i]
                return
        raise BookNotFoundError(f"Book {book_id} not found in session {session_id}")

    def clear_session(self, session_id: str) -> None:
        """Remove all books from a session."""
        self._sessions.pop(session_id, None)

    def session_exists(self, session_id: str) -> bool:
        """Check if session has any books."""
        return session_id in self._sessions and len(self._sessions[session_id]) > 0
