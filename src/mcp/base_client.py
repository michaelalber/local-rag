"""Base MCP client handling transport connections."""

import logging
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class BaseMCPClient:
    """Base MCP client with pluggable transport.

    Handles connection lifecycle for both stdio and HTTP transports.
    Provides generic tool calling interface for adapters.

    Args:
        transport: Transport protocol ("stdio" or "http")
        http_url: URL for HTTP transport (e.g., "https://example.com/api/mcp")
        http_timeout: Timeout in seconds for HTTP requests
        command: Command to run for stdio transport (e.g., "python")
        args: Arguments for stdio command (e.g., ["-m", "server"])
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

            logger.info("MCP client connected via %s transport", self.transport)

        except Exception as e:
            logger.error("Failed to connect MCP client: %s", e)
            await self.disconnect()
            raise ConnectionError(f"Failed to connect MCP client: {e}") from e

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
        logger.info("MCP client disconnected")

    async def health_check(self) -> bool:
        """Check if MCP connection is active and healthy.

        Returns:
            True if connected and responsive, False otherwise
        """
        if not self._session:
            return False

        try:
            await self._session.list_tools()
            return True
        except Exception as e:
            logger.warning("Health check failed: %s", e)
            return False

    async def list_tools(self) -> list[Any]:
        """List available tools from the MCP server.

        Returns:
            List of tool definitions
        """
        if not self._session:
            return []

        try:
            result = await self._session.list_tools()
            return list(result.tools) if result.tools else []
        except Exception as e:
            logger.error("Failed to list tools: %s", e)
            return []

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result content

        Raises:
            RuntimeError: If not connected
        """
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        result = await self._session.call_tool(name, arguments)
        return result

    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._session is not None
