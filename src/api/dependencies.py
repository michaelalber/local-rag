"""FastAPI dependency injection.

Singleton services are cached at module level for efficiency.
FastAPI Depends() functions provide the DI integration.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.embeddings import OllamaEmbedder, SentenceTransformerEmbedder
from src.llm import OllamaLLMClient
from src.mcp import AegisMCPClient
from src.parsers import FileValidator, TextChunker, get_parser
from src.services import BookIngestionService, QueryService, SessionManager
from src.vectorstore import ChromaVectorStore

from .config import MCPTransport, get_settings

logger = logging.getLogger(__name__)

# Known Ollama embedding models
OLLAMA_EMBEDDING_MODELS = {
    "nomic-embed-text",
    "nomic-embed-text:latest",
    "mxbai-embed-large",
    "mxbai-embed-large:latest",
    "all-minilm",
    "all-minilm:latest",
}

# Type alias for embedders
Embedder = OllamaEmbedder | SentenceTransformerEmbedder


# --- Cached singletons (expensive to create) ---


@lru_cache
def get_embedder_singleton() -> Embedder:
    """Get cached embedder instance, auto-detecting backend."""
    settings = get_settings()
    model = settings.embedding_model

    # Use Ollama for known Ollama models or models with `:` tag
    if model in OLLAMA_EMBEDDING_MODELS or ":" in model:
        return OllamaEmbedder(
            model_name=model,
            base_url=settings.ollama_base_url,
        )

    # Default to sentence-transformers for HuggingFace models
    return SentenceTransformerEmbedder(model_name=model)


@lru_cache
def get_vector_store_singleton() -> ChromaVectorStore:
    """Get cached vector store instance."""
    settings = get_settings()
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    return ChromaVectorStore(persist_dir=settings.chroma_persist_dir)


@lru_cache
def get_llm_client_singleton() -> OllamaLLMClient:
    """Get cached LLM client instance."""
    settings = get_settings()
    return OllamaLLMClient(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
    )


@lru_cache
def get_session_manager_singleton() -> SessionManager:
    """Get cached session manager (holds session data in memory)."""
    settings = get_settings()
    return SessionManager(max_books=settings.max_books_per_session)


# --- Aegis MCP Client (lazy async initialization) ---

_aegis_client: AegisMCPClient | None = None
_aegis_client_initialized: bool = False


def _create_aegis_client() -> AegisMCPClient | None:
    """Create Aegis MCP client based on configuration (not connected yet)."""
    settings = get_settings()

    if not settings.aegis_mcp_transport:
        return None

    if settings.aegis_mcp_transport == MCPTransport.STDIO:
        return AegisMCPClient(
            transport="stdio",
            command=settings.aegis_mcp_command,
            args=settings.aegis_mcp_args.split() if settings.aegis_mcp_args else [],
            working_dir=settings.aegis_mcp_working_dir,
        )
    else:  # HTTP
        return AegisMCPClient(
            transport="http",
            http_url=settings.aegis_mcp_url,
            http_timeout=settings.aegis_mcp_timeout,
        )


async def get_aegis_client() -> AegisMCPClient | None:
    """Get Aegis MCP client (lazily initialized on first request).

    Returns None if Aegis is not configured.
    """
    global _aegis_client, _aegis_client_initialized

    if _aegis_client_initialized:
        return _aegis_client

    _aegis_client = _create_aegis_client()
    _aegis_client_initialized = True

    if _aegis_client:
        try:
            await _aegis_client.connect()
            logger.info("Aegis MCP client connected successfully")
        except Exception as e:
            logger.error("Failed to connect Aegis MCP client: %s", e)
            _aegis_client = None

    return _aegis_client


async def shutdown_aegis_client() -> None:
    """Disconnect Aegis MCP client on shutdown."""
    global _aegis_client, _aegis_client_initialized

    if _aegis_client:
        try:
            await _aegis_client.disconnect()
            logger.info("Aegis MCP client disconnected")
        except Exception as e:
            logger.warning("Error disconnecting Aegis MCP client: %s", e)

    _aegis_client = None
    _aegis_client_initialized = False


# --- FastAPI dependency functions ---


def get_embedder() -> Embedder:
    """FastAPI dependency for embedder."""
    return get_embedder_singleton()


def get_vector_store() -> ChromaVectorStore:
    """FastAPI dependency for vector store."""
    return get_vector_store_singleton()


def get_llm_client() -> OllamaLLMClient:
    """FastAPI dependency for LLM client."""
    return get_llm_client_singleton()


def get_session_manager() -> SessionManager:
    """FastAPI dependency for session manager."""
    return get_session_manager_singleton()


def get_ingestion_service(
    embedder: Annotated[Embedder, Depends(get_embedder)],
    vector_store: Annotated[ChromaVectorStore, Depends(get_vector_store)],
) -> BookIngestionService:
    """FastAPI dependency for ingestion service."""
    settings = get_settings()
    return BookIngestionService(
        parser_factory=get_parser,
        chunker=TextChunker(
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        ),
        embedder=embedder,
        vector_store=vector_store,
        validator=FileValidator(max_size_mb=settings.max_file_size_mb),
    )


async def get_query_service(
    vector_store: Annotated[ChromaVectorStore, Depends(get_vector_store)],
    embedder: Annotated[Embedder, Depends(get_embedder)],
    llm_client: Annotated[OllamaLLMClient, Depends(get_llm_client)],
    aegis_client: Annotated[AegisMCPClient | None, Depends(get_aegis_client)],
) -> QueryService:
    """FastAPI dependency for query service."""
    settings = get_settings()
    return QueryService(
        vector_store=vector_store,
        embedder=embedder,
        llm_client=llm_client,
        neighbor_window=settings.neighbor_window,
        aegis_client=aegis_client,
    )
