"""FastAPI dependency injection."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.application.services import BookIngestionService, QueryService, SessionManager
from src.domain.interfaces import EmbeddingService, LLMClient, VectorStore
from src.infrastructure.embeddings import SentenceTransformerEmbedder
from src.infrastructure.llm import OllamaLLMClient
from src.infrastructure.parsers import FileValidator, TextChunker, get_parser
from src.infrastructure.vectorstore import ChromaVectorStore

from .config import Settings, get_settings


@lru_cache
def _get_embedder(settings: Settings) -> EmbeddingService:
    """Get cached embedder instance."""
    return SentenceTransformerEmbedder(model_name=settings.embedding_model)


def get_embedder(
    settings: Annotated[Settings, Depends(get_settings)]
) -> EmbeddingService:
    """Get embedder with injected settings."""
    return _get_embedder(settings)


@lru_cache
def _get_vector_store(settings: Settings) -> VectorStore:
    """Get cached vector store instance."""
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    return ChromaVectorStore(persist_dir=settings.chroma_persist_dir)


def get_vector_store(settings: Annotated[Settings, Depends(get_settings)]) -> VectorStore:
    """Get vector store with injected settings."""
    return _get_vector_store(settings)


@lru_cache
def _get_llm_client(settings: Settings) -> LLMClient:
    """Get cached LLM client instance."""
    return OllamaLLMClient(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
    )


def get_llm_client(settings: Annotated[Settings, Depends(get_settings)]) -> LLMClient:
    """Get LLM client with injected settings."""
    return _get_llm_client(settings)


@lru_cache
def _get_session_manager(settings: Settings) -> SessionManager:
    """Get cached session manager instance."""
    return SessionManager(max_books=settings.max_books_per_session)


def get_session_manager(
    settings: Annotated[Settings, Depends(get_settings)]
) -> SessionManager:
    """Get session manager with injected settings."""
    return _get_session_manager(settings)


def get_ingestion_service(
    settings: Annotated[Settings, Depends(get_settings)],
    embedder: Annotated[EmbeddingService, Depends(get_embedder)],
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
) -> BookIngestionService:
    """Get ingestion service with dependencies."""
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
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
    embedder: Annotated[EmbeddingService, Depends(get_embedder)],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
) -> QueryService:
    """Get query service with dependencies."""
    return QueryService(
        vector_store=vector_store,
        embedder=embedder,
        llm_client=llm_client,
    )
