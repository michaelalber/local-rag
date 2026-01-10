"""MCP Manager for handling multiple MCP server connections."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .adapters.base import MCPAdapter

logger = logging.getLogger(__name__)


class MCPManager:
    """Manages multiple MCP server connections.

    Provides a unified interface for:
    - Registering MCP adapters
    - Connection lifecycle management
    - Routing queries to appropriate adapters
    - Health checking all connections

    Example:
        manager = MCPManager()
        manager.register(AegisAdapter(client1))
        manager.register(MSLearnAdapter(client2))
        await manager.connect_all()

        context = await manager.search_context("compliance", "access control", top_k=5)
    """

    def __init__(self):
        """Initialize empty adapter registry."""
        self._adapters: dict[str, MCPAdapter] = {}

    def register(self, adapter: "MCPAdapter") -> None:
        """Register an adapter by its name.

        Args:
            adapter: MCPAdapter instance to register
        """
        self._adapters[adapter.name] = adapter
        logger.info("Registered MCP adapter: %s", adapter.name)

    def get(self, name: str) -> "MCPAdapter | None":
        """Get adapter by source name.

        Args:
            name: Source name (e.g., "compliance", "mslearn")

        Returns:
            Adapter instance or None if not found
        """
        return self._adapters.get(name)

    @property
    def adapters(self) -> dict[str, "MCPAdapter"]:
        """Get all registered adapters."""
        return self._adapters

    def available_sources(self) -> list[str]:
        """Get list of registered source names.

        Returns:
            List of source names
        """
        return list(self._adapters.keys())

    async def get_sources_status(self) -> list[dict]:
        """Get status of all registered sources.

        Returns:
            List of source status dictionaries with name, display_name, available
        """
        sources = []
        for adapter in self._adapters.values():
            available = await adapter.health_check()
            sources.append({
                "name": adapter.name,
                "display_name": adapter.display_name,
                "available": available,
            })
        return sources

    async def search_context(
        self, source: str, query: str, top_k: int = 5
    ) -> list[str]:
        """Get context from a specific source.

        Args:
            source: Source name to query
            query: Natural language search query
            top_k: Maximum number of results

        Returns:
            List of context strings from the source
        """
        adapter = self._adapters.get(source)
        if not adapter:
            logger.warning("Unknown MCP source: %s", source)
            return []

        return await adapter.search_context(query, top_k)

    async def search_all_sources(
        self, query: str, top_k: int = 5
    ) -> dict[str, list[str]]:
        """Query all registered sources.

        Args:
            query: Natural language search query
            top_k: Maximum number of results per source

        Returns:
            Dictionary mapping source names to their context lists
        """
        results = {}
        for name, adapter in self._adapters.items():
            try:
                context = await adapter.search_context(query, top_k)
                results[name] = context
            except Exception as e:
                logger.error("Failed to query %s: %s", name, e)
                results[name] = []
        return results

    async def connect_all(self) -> None:
        """Connect all registered adapters.

        Failures are logged but don't prevent other adapters from connecting.
        """
        for name, adapter in self._adapters.items():
            try:
                await adapter.connect()
                logger.info("Connected MCP adapter: %s", name)
            except Exception as e:
                logger.warning("Failed to connect %s: %s", name, e)

    async def disconnect_all(self) -> None:
        """Disconnect all adapters."""
        for name, adapter in self._adapters.items():
            try:
                await adapter.disconnect()
                logger.info("Disconnected MCP adapter: %s", name)
            except Exception as e:
                logger.warning("Error disconnecting %s: %s", name, e)

    def __len__(self) -> int:
        """Return number of registered adapters."""
        return len(self._adapters)

    def __bool__(self) -> bool:
        """Return True if any adapters are registered."""
        return len(self._adapters) > 0
