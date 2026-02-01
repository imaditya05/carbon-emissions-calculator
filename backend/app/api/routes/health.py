"""Health check endpoints."""

from fastapi import APIRouter

from app.core.config import settings
from app.db.mongodb import mongodb_client

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint.

    Returns:
        Health status.
    """
    return {"status": "healthy"}


@router.get("/detailed")
async def detailed_health_check() -> dict[str, str | bool]:
    """Detailed health check including database connectivity.

    Returns:
        Detailed health status with database connection status.
    """
    db_healthy = await mongodb_client.ping()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "version": settings.app_version,
        "environment": settings.environment,
    }
