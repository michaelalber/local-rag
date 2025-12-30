"""FastAPI dependency injection.

Singleton services are cached at module level for efficiency.
FastAPI Depends() functions provide the DI integration.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.embeddings import OllamaEmbedder, SentenceTransformerEmbedder
from src.llm import OllamaLLMClient
from src.parsers import FileValidator, TextChunker, get_parser
from src.services import BookIngestionService, QueryService, SessionManager
from src.vectorstore import ChromaVectorStore

from .config import get_settings

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


def get_query_service(
    vector_store: Annotated[ChromaVectorStore, Depends(get_vector_store)],
    embedder: Annotated[Embedder, Depends(get_embedder)],
    llm_client: Annotated[OllamaLLMClient, Depends(get_llm_client)],
) -> QueryService:
    """FastAPI dependency for query service."""
    settings = get_settings()
    return QueryService(
        vector_store=vector_store,
        embedder=embedder,
        llm_client=llm_client,
        neighbor_window=settings.neighbor_window,
    )
