"""MongoDB connection management using PyMongo's native async support."""

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings


class MongoDBClient:
    """MongoDB client singleton for managing database connections."""

    _client: AsyncMongoClient | None = None
    _database: AsyncDatabase | None = None

    @classmethod
    async def get_client(cls) -> AsyncMongoClient:
        """Get or create the MongoDB client instance."""
        if cls._client is None:
            cls._client = AsyncMongoClient(settings.mongodb_url)
        return cls._client

    @classmethod
    async def get_database(cls) -> AsyncDatabase:
        """Get or create the database instance."""
        if cls._database is None:
            client = await cls.get_client()
            cls._database = client[settings.mongodb_database]
        return cls._database

    @classmethod
    async def close(cls) -> None:
        """Close the MongoDB client connection."""
        if cls._client is not None:
            await cls._client.close()
            cls._client = None
            cls._database = None

    @classmethod
    async def ping(cls) -> bool:
        """Check if the database connection is healthy."""
        try:
            client = await cls.get_client()
            await client.admin.command("ping")
            return True
        except Exception:
            return False


# Convenience reference
mongodb_client = MongoDBClient


async def get_database() -> AsyncDatabase:
    """Get the database instance for dependency injection."""
    return await MongoDBClient.get_database()
