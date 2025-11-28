"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Check API health."""
    return {
        "status": "ok",
        "version": "0.1.0",
    }
