"""Aegis MCP adapter for security compliance queries."""

import json
import logging
from typing import Any

from .base import MCPAdapter

logger = logging.getLogger(__name__)


class AegisAdapter(MCPAdapter):
    """Adapter for Aegis MCP server.

    Provides access to security compliance frameworks including:
    - NIST 800-53
    - OWASP
    - DOE security controls
    """

    name = "compliance"
    display_name = "Compliance"

    async def search_context(self, query: str, top_k: int = 5) -> list[str]:
        """Search compliance controls matching query.

        Args:
            query: Natural language search query
            top_k: Maximum number of results to return

        Returns:
            List of formatted compliance control strings
        """
        if not self.client.is_connected:
            logger.warning("Aegis adapter not connected")
            return []

        try:
            result = await self.client.call_tool(
                "search_compliance",
                {
                    "query": query,
                    "top_k": top_k,
                },
            )
            return self._format_results(result)
        except Exception as e:
            logger.error("Failed to search compliance: %s", e)
            return []

    def _format_results(self, result: Any) -> list[str]:
        """Format MCP tool results as context strings.

        Args:
            result: Raw MCP tool result

        Returns:
            List of formatted context strings
        """
        context_strings: list[str] = []

        if not result or not result.content:
            return context_strings

        for item in result.content:
            try:
                # Handle TextContent responses
                if hasattr(item, "text"):
                    data = json.loads(item.text)
                    if isinstance(data, list):
                        for entry in data:
                            context_strings.append(self._format_control(entry))
                    else:
                        context_strings.append(self._format_control(data))
                # Handle dict responses
                elif isinstance(item, dict):
                    context_strings.append(self._format_control(item))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Failed to parse compliance result: %s", e)
                continue

        return context_strings

    def _format_control(self, control: dict[str, Any]) -> str:
        """Format a single control as a context string.

        Args:
            control: Control data dictionary

        Returns:
            Formatted context string
        """
        control_id = control.get("control_id", "Unknown")
        framework = control.get("framework", "Unknown")
        title = control.get("title", "")
        description = control.get("description", "")

        return (
            f"[Compliance Control: {control_id}]\n"
            f"Framework: {framework}\n"
            f"Title: {title}\n"
            f"Description: {description}"
        )
