"""Search history service for storing and retrieving user searches."""

import math
from datetime import datetime
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection

from app.db.mongodb import mongodb_client
from app.models.emission import TransportMode
from app.models.route import Coordinates, RouteInfo, ModeComparison
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
        self._collection: AsyncCollection | None = None

    async def _get_collection(self) -> AsyncCollection:
        """Get the searches collection lazily."""
        if self._collection is None:
            db = await mongodb_client.get_database()
            self._collection = db["searches"]
        return self._collection

    def _serialize_search(self, search: SearchCreate, user_id: str) -> dict[str, Any]:
        """Serialize a search for database insertion.
        
        Note: We exclude geometry from storage as it's large and not needed
        for search history display. Routes can be recomputed if needed.
        """
        # Create route dicts without geometry to save storage and improve query speed
        shortest = search.shortest_route.model_dump()
        shortest["geometry"] = []  # Don't store large geometry arrays
        
        efficient = search.efficient_route.model_dump()
        efficient["geometry"] = []  # Don't store large geometry arrays
        
        return {
            "user_id": user_id,
            "origin_name": search.origin_name,
            "origin_coordinates": search.origin_coordinates.model_dump(),
            "destination_name": search.destination_name,
            "destination_coordinates": search.destination_coordinates.model_dump(),
            "weight_kg": search.weight_kg,
            "shortest_route": shortest,
            "efficient_route": efficient,
            "mode_comparison": [mc.model_dump() for mc in search.mode_comparison],
            "created_at": datetime.utcnow(),
        }

    def _deserialize_search(self, doc: dict[str, Any]) -> SearchResponse:
        """Deserialize a database document to SearchResponse."""
        # Handle mode_comparison (may not exist in old records)
        mode_comparison = []
        if "mode_comparison" in doc:
            mode_comparison = [ModeComparison(**mc) for mc in doc["mode_comparison"]]

        # Ensure geometry exists (might be excluded by projection)
        shortest_data = doc["shortest_route"]
        if "geometry" not in shortest_data:
            shortest_data["geometry"] = []
            
        efficient_data = doc["efficient_route"]
        if "geometry" not in efficient_data:
            efficient_data["geometry"] = []

        return SearchResponse(
            id=str(doc["_id"]),
            origin_name=doc["origin_name"],
            origin_coordinates=Coordinates(**doc["origin_coordinates"]),
            destination_name=doc["destination_name"],
            destination_coordinates=Coordinates(**doc["destination_coordinates"]),
            weight_kg=doc["weight_kg"],
            shortest_route=RouteInfo(**shortest_data),
            efficient_route=RouteInfo(**efficient_data),
            mode_comparison=mode_comparison,
            created_at=doc["created_at"],
        )

    async def create_search(self, search: SearchCreate, user_id: str) -> SearchResponse:
        """Create a new search record."""
        collection = await self._get_collection()
        doc = self._serialize_search(search, user_id)

        result = await collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        return self._deserialize_search(doc)

    async def get_search_by_id(self, search_id: str, user_id: str) -> SearchResponse:
        """Get a specific search by ID."""
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
        """Get paginated search history for a user."""
        collection = await self._get_collection()

        # Build query
        query: dict[str, Any] = {"user_id": user_id}

        if filters:
            # Filter by shortest route transport mode
            if filters.shortest_mode:
                query["shortest_route.transport_mode"] = filters.shortest_mode.value

            # Filter by efficient route transport mode
            if filters.efficient_mode:
                query["efficient_route.transport_mode"] = filters.efficient_mode.value

            if filters.origin_name:
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
        # Use projection to exclude large geometry fields for faster queries
        projection = {
            "shortest_route.geometry": 0,
            "efficient_route.geometry": 0,
        }
        
        cursor = (
            collection.find(query, projection)
            .sort("created_at", -1)
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
        """Delete a search record."""
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
        """Delete all search history for a user."""
        collection = await self._get_collection()
        result = await collection.delete_many({"user_id": user_id})
        return result.deleted_count
