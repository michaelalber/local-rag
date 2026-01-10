"""Export Control MCP adapter for export compliance queries."""

import json
import logging
from typing import Any

from .base import MCPAdapter

logger = logging.getLogger(__name__)


class ExportControlAdapter(MCPAdapter):
    """Adapter for Export Control MCP server.

    Provides access to export compliance tools including:
    - EAR (Export Administration Regulations) search
    - ITAR (International Traffic in Arms Regulations) search
    - Sanctions screening (OFAC SDN, BIS Entity List, Denied Persons)
    - Export classification assistance
    """

    name = "export_control"
    display_name = "Export Control"

    async def search_context(self, query: str, top_k: int = 5) -> list[str]:
        """Search export regulations and compliance data matching query.

        Args:
            query: Natural language search query
            top_k: Maximum number of results to return

        Returns:
            List of formatted export control context strings
        """
        if not self.client.is_connected:
            logger.warning("Export Control adapter not connected")
            return []

        try:
            # Try regulation search first
            result = await self.client.call_tool("search_regulations", {
                "query": query,
                "top_k": top_k,
            })
            return self._format_results(result)
        except Exception as e:
            logger.error("Failed to search export regulations: %s", e)
            return []

    def _format_results(self, result: Any) -> list[str]:
        """Format MCP tool results as context strings.

        Args:
            result: Raw MCP tool result

        Returns:
            List of formatted context strings
        """
        context_strings = []

        if not result or not result.content:
            return context_strings

        for item in result.content:
            try:
                # Handle TextContent responses
                if hasattr(item, "text"):
                    data = json.loads(item.text)
                    if isinstance(data, list):
                        for entry in data:
                            context_strings.append(self._format_entry(entry))
                    else:
                        context_strings.append(self._format_entry(data))
                # Handle dict responses
                elif isinstance(item, dict):
                    context_strings.append(self._format_entry(item))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Failed to parse export control result: %s", e)
                continue

        return context_strings

    def _format_entry(self, entry: dict) -> str:
        """Format a single entry as a context string.

        Args:
            entry: Entry data dictionary

        Returns:
            Formatted context string
        """
        entry_type = entry.get("type", "Regulation")
        entry_id = entry.get("id", entry.get("control_id", "Unknown"))
        title = entry.get("title", "")
        description = entry.get("description", entry.get("text", ""))
        source = entry.get("source", entry.get("framework", ""))

        parts = [f"[Export Control: {entry_id}]"]
        if entry_type:
            parts.append(f"Type: {entry_type}")
        if source:
            parts.append(f"Source: {source}")
        if title:
            parts.append(f"Title: {title}")
        if description:
            parts.append(f"Description: {description}")

        return "\n".join(parts)
