"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.models import BookChatError

from .config import get_settings
from .dependencies import shutdown_aegis_client
from .exception_handlers import book_chat_error_handler, general_exception_handler
from .middleware import SecurityHeadersMiddleware
from .routes import books_router, chat_router, chat_stream_router, health_router, models_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    yield
    # Shutdown
    await shutdown_aegis_client()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="LocalBookChat",
        description="Chat with your eBooks using local LLM",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],  # Only required methods
        allow_headers=["Content-Type", "session-id"],  # Only required headers
    )

    # Exception handlers
    app.add_exception_handler(BookChatError, book_chat_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Routes
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(books_router, prefix=settings.api_prefix)
    app.include_router(chat_router, prefix=settings.api_prefix)
    app.include_router(chat_stream_router, prefix=settings.api_prefix)
    app.include_router(models_router, prefix=settings.api_prefix)

    return app


# Application instance for uvicorn
app = create_app()
