"""Tests for Export Control MCP adapter."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from src.mcp.adapters.export_control import ExportControlAdapter
from src.mcp.base_client import BaseMCPClient


class TestExportControlAdapterInit:
    """Tests for adapter initialization."""

    def test_adapter_has_correct_name(self):
        """Test adapter has correct name."""
        mock_client = MagicMock(spec=BaseMCPClient)
        adapter = ExportControlAdapter(mock_client)

        assert adapter.name == "export_control"

    def test_adapter_has_correct_display_name(self):
        """Test adapter has correct display name."""
        mock_client = MagicMock(spec=BaseMCPClient)
        adapter = ExportControlAdapter(mock_client)

        assert adapter.display_name == "Export Control"


class TestExportControlAdapterSearchContext:
    """Tests for search_context method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock MCP client."""
        client = MagicMock(spec=BaseMCPClient)
        client.is_connected = True
        client.call_tool = AsyncMock()
        return client

    @pytest.fixture
    def adapter(self, mock_client):
        """Create adapter with mock client."""
        return ExportControlAdapter(mock_client)

    @pytest.mark.asyncio
    async def test_search_context_returns_formatted_results(self, adapter, mock_client):
        """Test search_context returns formatted context strings."""
        # Mock MCP response
        mock_content = MagicMock()
        mock_content.text = (
            '[{"id": "EAR-734.2", "type": "Regulation", '
            '"title": "Items Controlled", '
            '"description": "Items controlled for export", '
            '"source": "EAR"}]'
        )

        mock_result = MagicMock()
        mock_result.content = [mock_content]
        mock_client.call_tool.return_value = mock_result

        results = await adapter.search_context("export regulations", top_k=5)

        assert len(results) == 1
        assert "[Export Control: EAR-734.2]" in results[0]
        assert "Type: Regulation" in results[0]
        assert "Source: EAR" in results[0]
        assert "Title: Items Controlled" in results[0]

        mock_client.call_tool.assert_called_once_with(
            "search_regulations", {"query": "export regulations", "top_k": 5}
        )

    @pytest.mark.asyncio
    async def test_search_context_handles_multiple_results(self, adapter, mock_client):
        """Test search_context handles multiple results."""
        mock_content = MagicMock()
        mock_content.text = (
            "["
            '{"id": "EAR-734.2", "type": "Regulation", "title": "Item 1", '
            '"description": "Description 1", "source": "EAR"},'
            '{"id": "ITAR-120.1", "type": "Regulation", "title": "Item 2", '
            '"description": "Description 2", "source": "ITAR"}'
            "]"
        )

        mock_result = MagicMock()
        mock_result.content = [mock_content]
        mock_client.call_tool.return_value = mock_result

        results = await adapter.search_context("export", top_k=10)

        assert len(results) == 2
        assert "[Export Control: EAR-734.2]" in results[0]
        assert "[Export Control: ITAR-120.1]" in results[1]

    @pytest.mark.asyncio
    async def test_search_context_returns_empty_when_not_connected(self, mock_client):
        """Test search_context returns empty list when not connected."""
        mock_client.is_connected = False
        adapter = ExportControlAdapter(mock_client)

        results = await adapter.search_context("test query")

        assert results == []
        mock_client.call_tool.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_context_returns_empty_on_error(self, adapter, mock_client):
        """Test search_context returns empty list on error."""
        mock_client.call_tool.side_effect = Exception("MCP error")

        results = await adapter.search_context("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_context_handles_empty_response(self, adapter, mock_client):
        """Test search_context handles empty response."""
        mock_result = MagicMock()
        mock_result.content = []
        mock_client.call_tool.return_value = mock_result

        results = await adapter.search_context("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_context_handles_null_response(self, adapter, mock_client):
        """Test search_context handles null response."""
        mock_client.call_tool.return_value = None

        results = await adapter.search_context("test query")

        assert results == []


class TestExportControlAdapterFormatEntry:
    """Tests for _format_entry method."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mock client."""
        mock_client = MagicMock(spec=BaseMCPClient)
        return ExportControlAdapter(mock_client)

    def test_format_entry_with_all_fields(self, adapter):
        """Test formatting entry with all fields."""
        entry = {
            "id": "EAR-734.2",
            "type": "Regulation",
            "title": "Export Control Classification",
            "description": "Classification of export controlled items",
            "source": "EAR",
        }

        result = adapter._format_entry(entry)

        assert "[Export Control: EAR-734.2]" in result
        assert "Type: Regulation" in result
        assert "Source: EAR" in result
        assert "Title: Export Control Classification" in result
        assert "Description: Classification of export controlled items" in result

    def test_format_entry_with_control_id_fallback(self, adapter):
        """Test formatting entry with control_id instead of id."""
        entry = {
            "control_id": "OFAC-123",
            "title": "Sanctions Entry",
            "description": "Sanctioned entity",
            "framework": "OFAC SDN",
        }

        result = adapter._format_entry(entry)

        assert "[Export Control: OFAC-123]" in result
        assert "Source: OFAC SDN" in result

    def test_format_entry_with_text_fallback(self, adapter):
        """Test formatting entry with text instead of description."""
        entry = {
            "id": "BIS-001",
            "text": "Entity list entry text",
        }

        result = adapter._format_entry(entry)

        assert "[Export Control: BIS-001]" in result
        assert "Description: Entity list entry text" in result

    def test_format_entry_with_minimal_fields(self, adapter):
        """Test formatting entry with minimal fields."""
        entry = {}

        result = adapter._format_entry(entry)

        assert "[Export Control: Unknown]" in result

    def test_format_entry_without_optional_fields(self, adapter):
        """Test formatting entry without optional fields."""
        entry = {
            "id": "TEST-1",
        }

        result = adapter._format_entry(entry)

        assert "[Export Control: TEST-1]" in result
        # Type defaults to "Regulation", but empty strings are not included
        assert "Source:" not in result
        assert "Title:" not in result
        assert "Description:" not in result
