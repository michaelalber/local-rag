"""API configuration."""

from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPTransport(str, Enum):
    """MCP transport protocol for Aegis connection."""

    STDIO = "stdio"
    HTTP = "http"


class Settings(BaseSettings):
    """Application settings from environment."""

    # Paths
    upload_dir: Path = Path("./data/uploads")
    chroma_persist_dir: Path = Path("./data/chroma")

    # Limits
    max_file_size_mb: int = 100  # Balanced limit for eBooks (technical books with images)
    max_books_per_session: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Models
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "gemma3:12b"
    ollama_base_url: str = "http://localhost:11434"

    # RAG
    top_k_chunks: int = 5
    neighbor_window: int = 1  # Number of neighboring chunks to include (±N)

    # API
    api_prefix: str = "/api"

    # Aegis MCP Integration (optional)
    aegis_mcp_transport: MCPTransport | None = None  # "stdio" or "http", None to disable

    # Aegis HTTP transport settings
    aegis_mcp_url: str = "http://localhost:8765/mcp"
    aegis_mcp_timeout: int = 30

    # Aegis stdio transport settings
    aegis_mcp_command: str = "python"
    aegis_mcp_args: str = "-m aegis_mcp.server"  # space-separated args
    aegis_mcp_working_dir: str | None = None

    # Microsoft Learn MCP Integration (optional, HTTP only)
    mslearn_mcp_enabled: bool = False
    mslearn_mcp_url: str = "https://learn.microsoft.com/api/mcp"
    mslearn_mcp_timeout: int = 30

    # Export Control MCP Integration (optional)
    export_control_mcp_transport: MCPTransport | None = None  # "stdio" or "http", None to disable

    # Export Control HTTP transport settings
    export_control_mcp_url: str = "http://localhost:8766/mcp"
    export_control_mcp_timeout: int = 30

    # Export Control stdio transport settings
    export_control_mcp_command: str = "uv"
    export_control_mcp_args: str = "run python -m export_control_mcp.server"
    export_control_mcp_working_dir: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (singleton)."""
    return Settings()
