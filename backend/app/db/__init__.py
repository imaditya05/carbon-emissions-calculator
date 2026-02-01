"""Database module for MongoDB connection and repositories."""

from app.db.mongodb import get_database, mongodb_client

__all__ = ["get_database", "mongodb_client"]
