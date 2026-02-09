"""Aegis MCP client supporting both stdio and HTTP transports."""

import logging
from typing import Any

from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client

from mcp import ClientSession

from .models import ComplianceSearchResult, ControlDetail

logger = logging.getLogger(__name__)


class AegisMCPClient:
    """Client for Aegis MCP server with pluggable transport.

    Supports two transport modes:
    - stdio: Spawns Aegis MCP as a subprocess (local only)
    - http: Connects to a running Aegis MCP server via HTTP

    Args:
        transport: Transport protocol ("stdio" or "http")
        http_url: URL for HTTP transport (e.g., "http://localhost:8765/mcp")
        http_timeout: Timeout in seconds for HTTP requests
        command: Command to run for stdio transport (e.g., "python")
        args: Arguments for stdio command (e.g., ["-m", "aegis_mcp.server"])
        working_dir: Working directory for stdio subprocess
    """

    def __init__(
        self,
        transport: str,
        http_url: str | None = None,
        http_timeout: int = 30,
        command: str | None = None,
        args: list[str] | None = None,
        working_dir: str | None = None,
    ):
        if transport not in ("stdio", "http"):
            raise ValueError(f"Invalid transport: {transport}. Must be 'stdio' or 'http'.")

        self.transport = transport
        self.http_url = http_url
        self.http_timeout = http_timeout
        self.command = command
        self.args = args or []
        self.working_dir = working_dir

        self._session: ClientSession | None = None
        self._context_manager: Any = None
        self._streams: Any = None

    async def connect(self) -> None:
        """Establish connection using configured transport.

        Raises:
            ConnectionError: If connection fails.
            ValueError: If required parameters are missing for the transport.
        """
        try:
            if self.transport == "stdio":
                if not self.command:
                    raise ValueError("command is required for stdio transport")

                self._context_manager = stdio_client(
                    StdioServerParameters(
                        command=self.command,
                        args=self.args,
                        cwd=self.working_dir,
                    )
                )
            else:  # http
                if not self.http_url:
                    raise ValueError("http_url is required for http transport")

                self._context_manager = streamablehttp_client(url=self.http_url)

            self._streams = await self._context_manager.__aenter__()
            read_stream, write_stream = self._streams[0], self._streams[1]

            self._session = ClientSession(read_stream, write_stream)
            await self._session.__aenter__()
            await self._session.initialize()

            logger.info("Connected to Aegis MCP via %s transport", self.transport)

        except Exception as e:
            logger.error("Failed to connect to Aegis MCP: %s", e)
            await self.disconnect()
            raise ConnectionError(f"Failed to connect to Aegis MCP: {e}") from e

    async def disconnect(self) -> None:
        """Close connection and cleanup resources."""
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception as e:
                logger.warning("Error closing MCP session: %s", e)
            self._session = None

        if self._context_manager:
            try:
                await self._context_manager.__aexit__(None, None, None)
            except Exception as e:
                logger.warning("Error closing MCP transport: %s", e)
            self._context_manager = None

        self._streams = None
        logger.info("Disconnected from Aegis MCP")

    async def search_compliance(
        self,
        query: str,
        frameworks: list[str] | None = None,
        top_k: int = 5,
    ) -> list[ComplianceSearchResult]:
        """Search compliance controls matching query.

        Args:
            query: Natural language search query
            frameworks: Filter by frameworks (e.g., ["nist-800-53", "owasp"])
            top_k: Maximum number of results to return

        Returns:
            List of matching compliance controls

        Raises:
            RuntimeError: If not connected
        """
        if not self._session:
            logger.warning("search_compliance called without active session")
            return []

        try:
            arguments: dict[str, Any] = {"query": query, "top_k": top_k}
            if frameworks:
                arguments["frameworks"] = frameworks

            result = await self._session.call_tool("search_compliance", arguments)

            # Parse results from MCP response
            results = []
            if result.content:
                for item in result.content:
                    # Handle both dict-like and object-like responses
                    if hasattr(item, "text"):
                        # TextContent - parse JSON
                        import json

                        data = json.loads(item.text)
                        if isinstance(data, list):
                            for entry in data:
                                results.append(ComplianceSearchResult(**entry))
                        else:
                            results.append(ComplianceSearchResult(**data))
                    elif isinstance(item, dict):
                        results.append(ComplianceSearchResult(**item))

            return results

        except Exception as e:
            logger.error("search_compliance failed: %s", e)
            return []

    async def get_control(self, control_id: str) -> ControlDetail | None:
        """Get detailed information about a specific control.

        Args:
            control_id: The control identifier (e.g., "AC-1", "SI-7")

        Returns:
            Control details or None if not found
        """
        if not self._session:
            logger.warning("get_control called without active session")
            return None

        try:
            result = await self._session.call_tool("get_control", {"control_id": control_id})

            if result.content:
                item = result.content[0]
                if hasattr(item, "text"):
                    import json

                    data = json.loads(item.text)
                    return ControlDetail(**data)
                elif isinstance(item, dict):
                    return ControlDetail(**item)

            return None

        except Exception as e:
            logger.error("get_control failed for %s: %s", control_id, e)
            return None

    async def health_check(self) -> bool:
        """Check if MCP connection is active and healthy.

        Returns:
            True if connected and responsive, False otherwise
        """
        if not self._session:
            return False

        try:
            # Try to list available tools as a health check
            await self._session.list_tools()
            return True
        except Exception as e:
            logger.warning("Health check failed: %s", e)
            return False

    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._session is not None
