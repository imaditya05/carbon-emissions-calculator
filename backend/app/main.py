"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health
from app.core.config import settings
from app.db.mongodb import mongodb_client
from app.db.init_db import init_collections


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events.

    Args:
        app: FastAPI application instance.

    Yields:
        None after startup, cleanup after shutdown.
    """
    # Startup: Initialize database and create indexes
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📦 Environment: {settings.environment}")
    print(f"🗄️  Connecting to database: {settings.mongodb_database}")

    db = await mongodb_client.get_database()
    await init_collections(db)

    yield

    # Shutdown: Close database connection
    await mongodb_client.close()
    print("👋 Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## Carbon Emission Calculator API

    Calculate carbon emissions for cargo transport between locations.

    ### Features
    - Route Computation: Find shortest and most efficient routes
    - Emission Calculation: Calculate CO2 emissions based on distance, weight, and transport mode
    - Search History: Store and retrieve previous searches
    - User Authentication: Secure JWT-based authentication
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint with API information.

    Returns:
        API name, version, and documentation links.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health",
    }
