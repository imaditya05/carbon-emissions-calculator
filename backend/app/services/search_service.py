"""Search history service for storing and retrieving user searches."""

import math
from datetime import datetime
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection

from app.db.mongodb import mongodb_client
from app.models.emission import TransportMode
from app.models.route import Coordinates, RouteInfo
from app.models.search import (
    PaginationMeta,
    SearchCreate,
    SearchFilters,
    SearchListResponse,
    SearchResponse,
)


class SearchServiceError(Exception):
    """Base exception for search service errors."""

    pass


class SearchNotFoundError(SearchServiceError):
    """Raised when a search record is not found."""

    pass


class SearchService:
    """Service for managing search history in MongoDB."""

    def __init__(self) -> None:
        """Initialize the search service."""
        self._collection: AsyncCollection | None = None

    async def _get_collection(self) -> AsyncCollection:
        """Get the searches collection lazily."""
        if self._collection is None:
            db = await mongodb_client.get_database()
            self._collection = db["searches"]
        return self._collection

    def _serialize_search(self, search: SearchCreate, user_id: str) -> dict[str, Any]:
        """Serialize a search for database insertion."""
        return {
            "user_id": user_id,
            "origin_name": search.origin_name,
            "origin_coordinates": search.origin_coordinates.model_dump(),
            "destination_name": search.destination_name,
            "destination_coordinates": search.destination_coordinates.model_dump(),
            "weight_kg": search.weight_kg,
            "transport_mode": search.transport_mode.value,
            "shortest_route": search.shortest_route.model_dump(),
            "efficient_route": search.efficient_route.model_dump(),
            "created_at": datetime.utcnow(),
        }

    def _deserialize_search(self, doc: dict[str, Any]) -> SearchResponse:
        """Deserialize a database document to SearchResponse."""
        return SearchResponse(
            id=str(doc["_id"]),
            origin_name=doc["origin_name"],
            origin_coordinates=Coordinates(**doc["origin_coordinates"]),
            destination_name=doc["destination_name"],
            destination_coordinates=Coordinates(**doc["destination_coordinates"]),
            weight_kg=doc["weight_kg"],
            transport_mode=TransportMode(doc["transport_mode"]),
            shortest_route=RouteInfo(**doc["shortest_route"]),
            efficient_route=RouteInfo(**doc["efficient_route"]),
            created_at=doc["created_at"],
        )

    async def create_search(self, search: SearchCreate, user_id: str) -> SearchResponse:
        """Create a new search record.

        Args:
            search: Search data to store.
            user_id: ID of the user who made the search.

        Returns:
            The created search record.
        """
        collection = await self._get_collection()
        doc = self._serialize_search(search, user_id)

        result = await collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        return self._deserialize_search(doc)

    async def get_search_by_id(self, search_id: str, user_id: str) -> SearchResponse:
        """Get a specific search by ID.

        Args:
            search_id: The search record ID.
            user_id: ID of the user (for authorization).

        Returns:
            The search record.

        Raises:
            SearchNotFoundError: If search not found or doesn't belong to user.
        """
        collection = await self._get_collection()

        try:
            object_id = ObjectId(search_id)
        except Exception:
            raise SearchNotFoundError(f"Invalid search ID: {search_id}")

        doc = await collection.find_one({"_id": object_id, "user_id": user_id})

        if not doc:
            raise SearchNotFoundError(f"Search with ID {search_id} not found")

        return self._deserialize_search(doc)

    async def get_user_searches(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
        filters: SearchFilters | None = None,
    ) -> SearchListResponse:
        """Get paginated search history for a user.

        Args:
            user_id: ID of the user.
            page: Page number (1-indexed).
            page_size: Number of items per page.
            filters: Optional filters to apply.

        Returns:
            Paginated list of searches.
        """
        collection = await self._get_collection()

        # Build query
        query: dict[str, Any] = {"user_id": user_id}

        if filters:
            if filters.transport_mode:
                query["transport_mode"] = filters.transport_mode.value

            if filters.origin_name:
                # Case-insensitive partial match
                query["origin_name"] = {"$regex": filters.origin_name, "$options": "i"}

            if filters.destination_name:
                query["destination_name"] = {
                    "$regex": filters.destination_name,
                    "$options": "i",
                }

            if filters.date_from or filters.date_to:
                date_query: dict[str, Any] = {}
                if filters.date_from:
                    date_query["$gte"] = filters.date_from
                if filters.date_to:
                    date_query["$lte"] = filters.date_to
                query["created_at"] = date_query

        # Get total count for pagination
        total = await collection.count_documents(query)

        # Calculate pagination
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        skip = (page - 1) * page_size

        # Fetch documents with pagination
        cursor = (
            collection.find(query)
            .sort("created_at", -1)  # Most recent first
            .skip(skip)
            .limit(page_size)
        )

        items = [self._deserialize_search(doc) async for doc in cursor]

        return SearchListResponse(
            items=items,
            pagination=PaginationMeta(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        )

    async def delete_search(self, search_id: str, user_id: str) -> bool:
        """Delete a search record.

        Args:
            search_id: The search record ID.
            user_id: ID of the user (for authorization).

        Returns:
            True if deleted successfully.

        Raises:
            SearchNotFoundError: If search not found or doesn't belong to user.
        """
        collection = await self._get_collection()

        try:
            object_id = ObjectId(search_id)
        except Exception:
            raise SearchNotFoundError(f"Invalid search ID: {search_id}")

        result = await collection.delete_one({"_id": object_id, "user_id": user_id})

        if result.deleted_count == 0:
            raise SearchNotFoundError(f"Search with ID {search_id} not found")

        return True

    async def delete_all_user_searches(self, user_id: str) -> int:
        """Delete all search history for a user.

        Args:
            user_id: ID of the user.

        Returns:
            Number of deleted records.
        """
        collection = await self._get_collection()
        result = await collection.delete_many({"user_id": user_id})
        return result.deleted_count
