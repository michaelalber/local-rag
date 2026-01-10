"""Microsoft Learn MCP adapter for documentation queries."""

import json
import logging
from typing import Any

from .base import MCPAdapter

logger = logging.getLogger(__name__)


class MSLearnAdapter(MCPAdapter):
    """Adapter for Microsoft Learn MCP server.

    Provides access to Microsoft's official documentation including:
    - Azure documentation
    - .NET documentation
    - Developer tools and frameworks
    - Code samples

    Endpoint: https://learn.microsoft.com/api/mcp
    """

    name = "mslearn"
    display_name = "MS Learn"

    async def search_context(self, query: str, top_k: int = 5) -> list[str]:
        """Search Microsoft Learn documentation.

        Args:
            query: Natural language search query
            top_k: Maximum number of results to return

        Returns:
            List of formatted documentation strings
        """
        if not self.client.is_connected:
            logger.warning("MS Learn adapter not connected")
            return []

        try:
            # MS Learn uses 'microsoft_docs_search' tool
            result = await self.client.call_tool("microsoft_docs_search", {
                "query": query,
                "count": top_k,
            })
            return self._format_results(result)
        except Exception as e:
            logger.error("Failed to search MS Learn: %s", e)
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
                            formatted = self._format_doc(entry)
                            if formatted:
                                context_strings.append(formatted)
                    elif isinstance(data, dict):
                        # Could be a single result or a container
                        if "results" in data:
                            for entry in data["results"]:
                                formatted = self._format_doc(entry)
                                if formatted:
                                    context_strings.append(formatted)
                        else:
                            formatted = self._format_doc(data)
                            if formatted:
                                context_strings.append(formatted)
                # Handle dict responses
                elif isinstance(item, dict):
                    formatted = self._format_doc(item)
                    if formatted:
                        context_strings.append(formatted)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Failed to parse MS Learn result: %s", e)
                continue

        return context_strings

    def _format_doc(self, doc: dict) -> str | None:
        """Format a single document as a context string.

        Args:
            doc: Document data dictionary

        Returns:
            Formatted context string or None if insufficient data
        """
        title = doc.get("title", "")
        description = doc.get("description", doc.get("summary", ""))
        url = doc.get("url", doc.get("link", ""))
        content = doc.get("content", doc.get("snippet", ""))

        if not title and not content:
            return None

        parts = [f"[Microsoft Learn: {title}]"] if title else ["[Microsoft Learn]"]

        if description:
            parts.append(f"Summary: {description}")

        if content:
            # Truncate long content
            if len(content) > 500:
                content = content[:500] + "..."
            parts.append(f"Content: {content}")

        if url:
            parts.append(f"URL: {url}")

        return "\n".join(parts)
