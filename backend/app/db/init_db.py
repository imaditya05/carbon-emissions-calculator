"""Database initialization - creates collections and indexes."""

from pymongo.asynchronous.database import AsyncDatabase


async def init_collections(db: AsyncDatabase) -> None:
    """Initialize database collections with proper indexes.

    Collections:
    - users: Store user accounts
    - searches: Store search history

    Args:
        db: MongoDB database instance.
    """
    # Get existing collections
    existing_collections = await db.list_collection_names()

    # Create 'users' collection if it doesn't exist
    if "users" not in existing_collections:
        await db.create_collection("users")
        print("✓ Created 'users' collection")

    # Create indexes for users collection
    users_collection = db["users"]
    await users_collection.create_index("email", unique=True)
    print("✓ Created unique index on users.email")

    # Create 'searches' collection if it doesn't exist
    if "searches" not in existing_collections:
        await db.create_collection("searches")
        print("✓ Created 'searches' collection")

    # Create indexes for searches collection
    searches_collection = db["searches"]

    # Index for user's searches (most common query)
    await searches_collection.create_index("user_id")
    print("✓ Created index on searches.user_id")

    # Index for sorting by date
    await searches_collection.create_index("created_at")
    print("✓ Created index on searches.created_at")

    # Compound index for user searches sorted by date
    await searches_collection.create_index([
        ("user_id", 1),
        ("created_at", -1),
    ])
    print("✓ Created compound index on searches(user_id, created_at)")

    # Index for filtering by transport mode
    await searches_collection.create_index([
        ("user_id", 1),
        ("transport_mode", 1),
    ])
    print("✓ Created compound index on searches(user_id, transport_mode)")

    print("\n🗄️  Database initialization complete!")


async def get_collection_stats(db: AsyncDatabase) -> dict[str, int]:
    """Get document counts for all collections.

    Args:
        db: MongoDB database instance.

    Returns:
        Dictionary with collection names and document counts.
    """
    stats = {}
    collections = await db.list_collection_names()

    for collection_name in collections:
        count = await db[collection_name].count_documents({})
        stats[collection_name] = count

    return stats
