"""Health check endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from src.mcp import MCPManager

from ..dependencies import get_mcp_manager

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    mcp_manager: Annotated[MCPManager, Depends(get_mcp_manager)],
) -> dict[str, Any]:
    """Check API health including all MCP source statuses."""
    # Get status of all registered MCP sources
    mcp_sources = await mcp_manager.get_sources_status()

    return {
        "status": "ok",
        "version": "0.1.0",
        "mcp_sources": mcp_sources,
    }
