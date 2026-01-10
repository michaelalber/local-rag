"""Health check endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from src.mcp import AegisMCPClient

from ..config import get_settings
from ..dependencies import get_aegis_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    aegis_client: Annotated[AegisMCPClient | None, Depends(get_aegis_client)],
) -> dict:
    """Check API health including Aegis MCP status."""
    settings = get_settings()

    # Check Aegis availability
    aegis_available = False
    if aegis_client:
        aegis_available = await aegis_client.health_check()

    return {
        "status": "ok",
        "version": "0.1.0",
        "aegis_available": aegis_available,
        "aegis_transport": settings.aegis_mcp_transport.value if settings.aegis_mcp_transport else None,
    }
