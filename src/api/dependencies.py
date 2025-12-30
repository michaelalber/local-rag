"""FastAPI dependency injection."""

from functools import lru_cache
from typing import Annotated, Union

from fastapi import Depends

from src.embeddings import OllamaEmbedder, SentenceTransformerEmbedder
from src.llm import OllamaLLMClient
from src.parsers import FileValidator, TextChunker, get_parser
from src.services import BookIngestionService, QueryService, SessionManager
from src.vectorstore import ChromaVectorStore

from .config import Settings, get_settings

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
Embedder = Union[OllamaEmbedder, SentenceTransformerEmbedder]


@lru_cache
def _get_embedder(settings: Settings) -> Embedder:
    """Get cached embedder instance, auto-detecting backend."""
    model = settings.embedding_model

    # Use Ollama for known Ollama models or models with `:` tag
    if model in OLLAMA_EMBEDDING_MODELS or ":" in model:
        return OllamaEmbedder(
            model_name=model,
            base_url=settings.ollama_base_url,
        )

    # Default to sentence-transformers for HuggingFace models
    return SentenceTransformerEmbedder(model_name=model)


def get_embedder(
    settings: Annotated[Settings, Depends(get_settings)]
) -> Embedder:
    """Get embedder with injected settings."""
    return _get_embedder(settings)


@lru_cache
def _get_vector_store(settings: Settings) -> ChromaVectorStore:
    """Get cached vector store instance."""
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    return ChromaVectorStore(persist_dir=settings.chroma_persist_dir)


def get_vector_store(settings: Annotated[Settings, Depends(get_settings)]) -> ChromaVectorStore:
    """Get vector store with injected settings."""
    return _get_vector_store(settings)


@lru_cache
def _get_llm_client(settings: Settings) -> OllamaLLMClient:
    """Get cached LLM client instance."""
    return OllamaLLMClient(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
    )


def get_llm_client(settings: Annotated[Settings, Depends(get_settings)]) -> OllamaLLMClient:
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
    embedder: Annotated[Embedder, Depends(get_embedder)],
    vector_store: Annotated[ChromaVectorStore, Depends(get_vector_store)],
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
    settings: Annotated[Settings, Depends(get_settings)],
    vector_store: Annotated[ChromaVectorStore, Depends(get_vector_store)],
    embedder: Annotated[Embedder, Depends(get_embedder)],
    llm_client: Annotated[OllamaLLMClient, Depends(get_llm_client)],
) -> QueryService:
    """Get query service with dependencies."""
    return QueryService(
        vector_store=vector_store,
        embedder=embedder,
        llm_client=llm_client,
        neighbor_window=settings.neighbor_window,
    )
