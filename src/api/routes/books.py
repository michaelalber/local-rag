"""Book management endpoints."""

import shutil
import tempfile
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status

from src.services import BookIngestionService, SessionManager
from src.vectorstore import ChromaVectorStore

from ..dependencies import get_ingestion_service, get_session_manager, get_vector_store
from ..schemas import BookResponse

router = APIRouter(prefix="/books", tags=["books"])

ALLOWED_EXTENSIONS = {".pdf", ".epub", ".md", ".txt", ".rst", ".html"}


@router.post("", status_code=status.HTTP_201_CREATED, response_model=list[BookResponse])
async def upload_books(
    files: Annotated[list[UploadFile], File(...)],
    session_id: Annotated[str, Header()],
    ingestion_service: Annotated[BookIngestionService, Depends(get_ingestion_service)],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> list[BookResponse]:
    """
    Upload one or more books.

    Files are validated, parsed, chunked, embedded, and stored.
    """
    books = []

    for upload_file in files:
        # Validate extension against allowlist to prevent path traversal
        raw_name = Path(upload_file.filename or "file").name
        ext = Path(raw_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {ext}",
            )
        # Use validated literal suffix from allowlist (breaks taint chain)
        safe_suffix = next(s for s in ALLOWED_EXTENSIONS if s == ext)

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=safe_suffix) as tmp:
            shutil.copyfileobj(upload_file.file, tmp)
            tmp_path = Path(tmp.name)

        try:
            # Ingest the book
            book = await ingestion_service.ingest_book(
                file_path=tmp_path,
                session_id=session_id,
                original_filename=upload_file.filename,
            )

            # Add to session
            session_manager.add_book(session_id, book)

            books.append(
                BookResponse(
                    id=book.id,
                    title=book.title,
                    author=book.author,
                    file_type=book.file_type,
                    chunk_count=book.chunk_count,
                )
            )
        finally:
            # Clean up temp file
            tmp_path.unlink(missing_ok=True)

    return books


@router.get("", response_model=list[BookResponse])
async def list_books(
    session_id: Annotated[str, Header()],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> list[BookResponse]:
    """List all books in the current session."""
    books = session_manager.get_books(session_id)

    return [
        BookResponse(
            id=book.id,
            title=book.title,
            author=book.author,
            file_type=book.file_type,
            chunk_count=book.chunk_count,
        )
        for book in books
    ]


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: UUID,
    session_id: Annotated[str, Header()],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
    vector_store: Annotated[ChromaVectorStore, Depends(get_vector_store)],
) -> None:
    """Remove a book from the session and delete its chunks from the vector store."""
    session_manager.remove_book(session_id, book_id)
    await vector_store.delete_book_chunks(session_id, book_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_session(
    session_id: Annotated[str, Header()],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
    vector_store: Annotated[ChromaVectorStore, Depends(get_vector_store)],
) -> None:
    """Clear all books from the session."""
    session_manager.clear_session(session_id)
    await vector_store.delete_collection(session_id)
