"""Authentication service for user registration and login."""

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Token, UserCreate, UserResponse


class AuthServiceError(Exception):
    """Base exception for auth service errors."""

    pass


class UserAlreadyExistsError(AuthServiceError):
    """Raised when attempting to register with an existing email."""

    pass


class InvalidCredentialsError(AuthServiceError):
    """Raised when login credentials are invalid."""

    pass


class UserNotFoundError(AuthServiceError):
    """Raised when a user is not found."""

    pass


class AuthService:
    """Service for handling user authentication operations."""

    def __init__(self, db: AsyncDatabase) -> None:
        """Initialize the auth service with database connection.

        Args:
            db: MongoDB database instance.
        """
        self.db = db
        self.collection = db["users"]

    async def register_user(self, user_data: UserCreate) -> Token:
        """Register a new user.

        Args:
            user_data: User registration data.

        Returns:
            JWT token with user information.

        Raises:
            UserAlreadyExistsError: If email is already registered.
        """
        # Check if user already exists
        existing_user = await self.collection.find_one({"email": user_data.email})
        if existing_user:
            raise UserAlreadyExistsError(
                f"User with email {user_data.email} already exists"
            )

        # Create user document
        user_doc: dict[str, Any] = {
            "email": user_data.email,
            "hashed_password": hash_password(user_data.password),
            "full_name": user_data.full_name,
            "created_at": datetime.now(timezone.utc),
            "is_active": True,
        }

        # Insert into database
        result = await self.collection.insert_one(user_doc)
        user_id = str(result.inserted_id)

        # Create response
        user_response = UserResponse(
            id=user_id,
            email=user_data.email,
            full_name=user_data.full_name,
            created_at=user_doc["created_at"],
            is_active=True,
        )

        # Generate token
        access_token = create_access_token(
            data={"sub": user_id, "email": user_data.email}
        )

        return Token(access_token=access_token, user=user_response)

    async def login_user(self, email: str, password: str) -> Token:
        """Authenticate a user and return a token.

        Args:
            email: User email.
            password: Plain text password.

        Returns:
            JWT token with user information.

        Raises:
            InvalidCredentialsError: If credentials are invalid.
        """
        # Find user by email
        user_doc = await self.collection.find_one({"email": email})
        if not user_doc:
            raise InvalidCredentialsError("Invalid email or password")

        # Verify password
        if not verify_password(password, user_doc["hashed_password"]):
            raise InvalidCredentialsError("Invalid email or password")

        # Check if user is active
        if not user_doc.get("is_active", True):
            raise InvalidCredentialsError("User account is deactivated")

        user_id = str(user_doc["_id"])

        # Create response
        user_response = UserResponse(
            id=user_id,
            email=user_doc["email"],
            full_name=user_doc["full_name"],
            created_at=user_doc["created_at"],
            is_active=user_doc.get("is_active", True),
        )

        # Generate token
        access_token = create_access_token(
            data={"sub": user_id, "email": email}
        )

        return Token(access_token=access_token, user=user_response)

    async def get_user_by_id(self, user_id: str) -> UserResponse | None:
        """Get a user by their ID.

        Args:
            user_id: The user's ObjectId as a string.

        Returns:
            UserResponse if found, None otherwise.
        """
        try:
            user_doc = await self.collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

        if not user_doc:
            return None

        return UserResponse(
            id=str(user_doc["_id"]),
            email=user_doc["email"],
            full_name=user_doc["full_name"],
            created_at=user_doc["created_at"],
            is_active=user_doc.get("is_active", True),
        )
