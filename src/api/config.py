"""API configuration."""

from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment."""

    # Paths
    upload_dir: Path = Path("./data/uploads")
    chroma_persist_dir: Path = Path("./data/chroma")

    # Limits
    max_file_size_mb: int = 50  # Reduced from 150MB for security
    max_books_per_session: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Models
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "mistral:7b-instruct-q4_K_M"
    ollama_base_url: str = "http://localhost:11434"

    # RAG
    top_k_chunks: int = 5
    neighbor_window: int = 1  # Number of neighboring chunks to include (±N)

    # API
    api_prefix: str = "/api"

    model_config = ConfigDict(env_file=".env", extra="ignore", frozen=True)


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
