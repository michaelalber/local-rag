"""Base MCP adapter interface."""

from abc import ABC, abstractmethod

from ..base_client import BaseMCPClient


class MCPAdapter(ABC):
    """Abstract base adapter for MCP servers.

    Each adapter wraps a BaseMCPClient and provides a unified interface
    for retrieving context from the specific MCP server.

    Attributes:
        name: Internal identifier for the source (e.g., "compliance", "mslearn")
        display_name: Human-readable name for UI display
    """

    name: str
    display_name: str

    def __init__(self, client: BaseMCPClient):
        """Initialize adapter with an MCP client.

        Args:
            client: Configured BaseMCPClient instance
        """
        self.client = client

    @abstractmethod
    async def search_context(self, query: str, top_k: int = 5) -> list[str]:
        """Search and return formatted context strings for RAG.

        Args:
            query: Natural language search query
            top_k: Maximum number of results to return

        Returns:
            List of formatted context strings suitable for LLM consumption
        """
        pass

    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        await self.client.connect()

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        await self.client.disconnect()

    async def health_check(self) -> bool:
        """Check if the MCP connection is healthy.

        Returns:
            True if connected and responsive, False otherwise
        """
        return await self.client.health_check()

    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self.client.is_connected
