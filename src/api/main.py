"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.domain.exceptions import BookChatError

from .config import get_settings
from .exception_handlers import book_chat_error_handler
from .routes import books_router, chat_router, health_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="LocalBookChat",
        description="Chat with your eBooks using local LLM",
        version="0.1.0",
    )

    # CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    app.add_exception_handler(BookChatError, book_chat_error_handler)

    # Routes
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(books_router, prefix=settings.api_prefix)
    app.include_router(chat_router, prefix=settings.api_prefix)

    return app


# Application instance for uvicorn
app = create_app()
