"""MCP client integration for external knowledge sources."""

from .adapters import AegisAdapter, ExportControlAdapter, MCPAdapter, MSLearnAdapter

# Backward compatibility - AegisMCPClient is now replaced by AegisAdapter + BaseMCPClient
# but keep the old import working during transition
from .aegis_client import AegisMCPClient
from .base_client import BaseMCPClient
from .manager import MCPManager
from .models import ComplianceSearchResult, ControlDetail

__all__ = [
    "AegisAdapter",
    "AegisMCPClient",
    "BaseMCPClient",
    "ComplianceSearchResult",
    "ControlDetail",
    "ExportControlAdapter",
    "MCPAdapter",
    "MCPManager",
    "MSLearnAdapter",
]
