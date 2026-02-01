"""User-related Pydantic models for authentication and user management."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration request."""

    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]
    full_name: Annotated[str, Field(min_length=1, max_length=100)]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "full_name": "John Doe",
            }
        }
    )


class UserResponse(BaseModel):
    """Schema for user response (excludes sensitive data)."""

    id: str
    email: EmailStr
    full_name: str
    created_at: datetime
    is_active: bool = True

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "email": "user@example.com",
                "full_name": "John Doe",
                "created_at": "2024-01-01T00:00:00Z",
                "is_active": True,
            }
        },
    )


class UserInDB(BaseModel):
    """Schema for user stored in database."""

    email: EmailStr
    hashed_password: str
    full_name: str
    created_at: datetime
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema for decoded JWT token data."""

    user_id: str | None = None
    email: str | None = None
