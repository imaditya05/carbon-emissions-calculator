"""Health check endpoints."""

from fastapi import APIRouter

from app.core.config import settings

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
    """Detailed health check with application info.

    Returns:
        Detailed health status with version and environment.
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }
