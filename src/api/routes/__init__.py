"""API routes."""

from .books import router as books_router
from .chat import router as chat_router
from .chat_stream import router as chat_stream_router
from .health import router as health_router
from .models import router as models_router

__all__ = ["health_router", "books_router", "chat_router", "chat_stream_router", "models_router"]
