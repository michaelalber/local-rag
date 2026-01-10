"""Tests for Aegis MCP client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mcp.aegis_client import AegisMCPClient
from src.mcp.models import ComplianceSearchResult, ControlDetail


class TestAegisMCPClientInit:
    """Tests for client initialization."""

    def test_init_with_stdio_transport(self):
        """Test initialization with stdio transport."""
        client = AegisMCPClient(
            transport="stdio",
            command="python",
            args=["-m", "aegis_mcp.server"],
            working_dir="/path/to/aegis",
        )

        assert client.transport == "stdio"
        assert client.command == "python"
        assert client.args == ["-m", "aegis_mcp.server"]
        assert client.working_dir == "/path/to/aegis"
        assert not client.is_connected

    def test_init_with_http_transport(self):
        """Test initialization with HTTP transport."""
        client = AegisMCPClient(
            transport="http",
            http_url="http://localhost:8765/mcp",
            http_timeout=60,
        )

        assert client.transport == "http"
        assert client.http_url == "http://localhost:8765/mcp"
        assert client.http_timeout == 60
        assert not client.is_connected

    def test_init_with_invalid_transport_raises(self):
        """Test that invalid transport raises ValueError."""
        with pytest.raises(ValueError, match="Invalid transport"):
            AegisMCPClient(transport="invalid")


class TestAegisMCPClientConnect:
    """Tests for connection handling."""

    @pytest.fixture
    def mock_stdio_client(self):
        """Mock stdio_client context manager."""
        with patch("src.mcp.aegis_client.stdio_client") as mock:
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = (AsyncMock(), AsyncMock(), None)
            mock.return_value = mock_cm
            yield mock

    @pytest.fixture
    def mock_http_client(self):
        """Mock streamablehttp_client context manager."""
        with patch("src.mcp.aegis_client.streamablehttp_client") as mock:
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = (AsyncMock(), AsyncMock(), None)
            mock.return_value = mock_cm
            yield mock

    @pytest.fixture
    def mock_client_session(self):
        """Mock ClientSession."""
        with patch("src.mcp.aegis_client.ClientSession") as mock:
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session.initialize = AsyncMock()
            mock.return_value = mock_session
            yield mock

    @pytest.mark.asyncio
    async def test_connect_stdio_success(
        self, mock_stdio_client, mock_client_session
    ):
        """Test successful connection via stdio."""
        client = AegisMCPClient(
            transport="stdio",
            command="python",
            args=["-m", "aegis_mcp.server"],
        )

        await client.connect()

        assert client.is_connected
        mock_stdio_client.assert_called_once()
        mock_client_session.return_value.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_http_success(
        self, mock_http_client, mock_client_session
    ):
        """Test successful connection via HTTP."""
        client = AegisMCPClient(
            transport="http",
            http_url="http://localhost:8765/mcp",
        )

        await client.connect()

        assert client.is_connected
        mock_http_client.assert_called_once_with(url="http://localhost:8765/mcp")

    @pytest.mark.asyncio
    async def test_connect_stdio_missing_command_raises(self):
        """Test that missing command for stdio raises ValueError."""
        client = AegisMCPClient(transport="stdio")

        with pytest.raises(ConnectionError, match="command is required"):
            await client.connect()

    @pytest.mark.asyncio
    async def test_connect_http_missing_url_raises(self):
        """Test that missing URL for HTTP raises ValueError."""
        client = AegisMCPClient(transport="http")

        with pytest.raises(ConnectionError, match="http_url is required"):
            await client.connect()

    @pytest.mark.asyncio
    async def test_disconnect_cleans_up(
        self, mock_stdio_client, mock_client_session
    ):
        """Test that disconnect cleans up resources."""
        client = AegisMCPClient(
            transport="stdio",
            command="python",
        )

        await client.connect()
        assert client.is_connected

        await client.disconnect()
        assert not client.is_connected


class TestAegisMCPClientSearchCompliance:
    """Tests for search_compliance method."""

    @pytest.fixture
    def connected_client(self):
        """Create a client with mocked session."""
        client = AegisMCPClient(transport="http", http_url="http://test/mcp")
        client._session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_search_compliance_returns_results(self, connected_client):
        """Test search_compliance returns parsed results."""
        # Mock MCP response
        mock_content = MagicMock()
        mock_content.text = (
            '[{"control_id": "AC-1", "title": "Access Control Policy", '
            '"description": "Establish access control policy", '
            '"framework": "nist-800-53", "relevance_score": 0.95}]'
        )

        mock_result = MagicMock()
        mock_result.content = [mock_content]
        connected_client._session.call_tool.return_value = mock_result

        results = await connected_client.search_compliance("access control", top_k=5)

        assert len(results) == 1
        assert results[0].control_id == "AC-1"
        assert results[0].title == "Access Control Policy"
        assert results[0].framework == "nist-800-53"
        assert results[0].relevance_score == 0.95

        connected_client._session.call_tool.assert_called_once_with(
            "search_compliance", {"query": "access control", "top_k": 5}
        )

    @pytest.mark.asyncio
    async def test_search_compliance_with_frameworks_filter(self, connected_client):
        """Test search_compliance passes frameworks filter."""
        mock_result = MagicMock()
        mock_result.content = []
        connected_client._session.call_tool.return_value = mock_result

        await connected_client.search_compliance(
            "password", frameworks=["nist-800-53", "owasp"], top_k=10
        )

        connected_client._session.call_tool.assert_called_once_with(
            "search_compliance",
            {"query": "password", "top_k": 10, "frameworks": ["nist-800-53", "owasp"]},
        )

    @pytest.mark.asyncio
    async def test_search_compliance_without_session_returns_empty(self):
        """Test search_compliance returns empty list when not connected."""
        client = AegisMCPClient(transport="http", http_url="http://test/mcp")

        results = await client.search_compliance("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_compliance_handles_error_gracefully(self, connected_client):
        """Test search_compliance handles errors gracefully."""
        connected_client._session.call_tool.side_effect = Exception("MCP error")

        results = await connected_client.search_compliance("test query")

        assert results == []


class TestAegisMCPClientGetControl:
    """Tests for get_control method."""

    @pytest.fixture
    def connected_client(self):
        """Create a client with mocked session."""
        client = AegisMCPClient(transport="http", http_url="http://test/mcp")
        client._session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_get_control_returns_detail(self, connected_client):
        """Test get_control returns control detail."""
        mock_content = MagicMock()
        mock_content.text = (
            '{"control_id": "AC-1", "title": "Access Control Policy", '
            '"description": "Establish policy", "framework": "nist-800-53", '
            '"requirements": ["Req 1", "Req 2"], '
            '"guidance": "Implementation guidance"}'
        )

        mock_result = MagicMock()
        mock_result.content = [mock_content]
        connected_client._session.call_tool.return_value = mock_result

        result = await connected_client.get_control("AC-1")

        assert result is not None
        assert result.control_id == "AC-1"
        assert result.title == "Access Control Policy"
        assert result.requirements == ["Req 1", "Req 2"]
        assert result.guidance == "Implementation guidance"

    @pytest.mark.asyncio
    async def test_get_control_not_found_returns_none(self, connected_client):
        """Test get_control returns None when not found."""
        mock_result = MagicMock()
        mock_result.content = []
        connected_client._session.call_tool.return_value = mock_result

        result = await connected_client.get_control("INVALID-1")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_control_without_session_returns_none(self):
        """Test get_control returns None when not connected."""
        client = AegisMCPClient(transport="http", http_url="http://test/mcp")

        result = await client.get_control("AC-1")

        assert result is None


class TestAegisMCPClientHealthCheck:
    """Tests for health_check method."""

    @pytest.fixture
    def connected_client(self):
        """Create a client with mocked session."""
        client = AegisMCPClient(transport="http", http_url="http://test/mcp")
        client._session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_health_check_returns_true_when_healthy(self, connected_client):
        """Test health_check returns True when connected."""
        connected_client._session.list_tools.return_value = []

        result = await connected_client.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_returns_false_when_not_connected(self):
        """Test health_check returns False when not connected."""
        client = AegisMCPClient(transport="http", http_url="http://test/mcp")

        result = await client.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_returns_false_on_error(self, connected_client):
        """Test health_check returns False on error."""
        connected_client._session.list_tools.side_effect = Exception("Connection lost")

        result = await connected_client.health_check()

        assert result is False


class TestComplianceSearchResult:
    """Tests for ComplianceSearchResult dataclass."""

    def test_create_result(self):
        """Test creating a ComplianceSearchResult."""
        result = ComplianceSearchResult(
            control_id="AC-1",
            title="Access Control Policy",
            description="Establish access control policy",
            framework="nist-800-53",
            relevance_score=0.95,
        )

        assert result.control_id == "AC-1"
        assert result.title == "Access Control Policy"
        assert result.relevance_score == 0.95


class TestControlDetail:
    """Tests for ControlDetail dataclass."""

    def test_create_detail_with_guidance(self):
        """Test creating a ControlDetail with guidance."""
        detail = ControlDetail(
            control_id="AC-1",
            title="Access Control Policy",
            description="Establish access control policy",
            framework="nist-800-53",
            requirements=["Req 1", "Req 2"],
            guidance="Implementation guidance",
        )

        assert detail.control_id == "AC-1"
        assert detail.requirements == ["Req 1", "Req 2"]
        assert detail.guidance == "Implementation guidance"

    def test_create_detail_without_guidance(self):
        """Test creating a ControlDetail without guidance."""
        detail = ControlDetail(
            control_id="AC-1",
            title="Access Control Policy",
            description="Establish access control policy",
            framework="nist-800-53",
            requirements=[],
        )

        assert detail.guidance is None
