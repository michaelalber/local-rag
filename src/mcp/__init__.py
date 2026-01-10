"""MCP client integration for external knowledge sources."""

from .base_client import BaseMCPClient
from .manager import MCPManager
from .models import ComplianceSearchResult, ControlDetail
from .adapters import MCPAdapter, AegisAdapter, MSLearnAdapter

# Backward compatibility - AegisMCPClient is now replaced by AegisAdapter + BaseMCPClient
# but keep the old import working during transition
from .aegis_client import AegisMCPClient

__all__ = [
    # New architecture
    "BaseMCPClient",
    "MCPManager",
    "MCPAdapter",
    "AegisAdapter",
    "MSLearnAdapter",
    # Models
    "ComplianceSearchResult",
    "ControlDetail",
    # Legacy (deprecated)
    "AegisMCPClient",
]
