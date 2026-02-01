"""Authentication endpoints for user registration and login.

Following FastAPI official documentation:
https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import CurrentUser
from app.db.mongodb import get_database
from app.models.user import Token, UserCreate, UserResponse
from app.services.auth_service import (
    AuthService,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account and return an access token.",
)
async def register(user_data: UserCreate) -> Token:
    """Register a new user.

    Args:
        user_data: User registration data including email, password, and name.

    Returns:
        JWT token with user information.

    Raises:
        HTTPException: If email is already registered.
    """
    db = await get_database()
    auth_service = AuthService(db)

    try:
        return await auth_service.register_user(user_data)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/token",
    response_model=Token,
    summary="Login for access token",
    description="OAuth2 compatible token login, get an access token for future requests.",
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """OAuth2 compatible login endpoint.

    Uses form data (username/password) as per OAuth2 specification.
    The 'username' field accepts email address.

    Args:
        form_data: OAuth2 password request form with username and password.

    Returns:
        JWT token with user information.

    Raises:
        HTTPException: If credentials are invalid.
    """
    db = await get_database()
    auth_service = AuthService(db)

    try:
        # OAuth2 uses 'username' field, but we accept email
        return await auth_service.login_user(
            email=form_data.username,
            password=form_data.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's information.",
)
async def get_current_user_info(current_user: CurrentUser) -> UserResponse:
    """Get the current authenticated user's information.

    Args:
        current_user: The authenticated user from the JWT token.

    Returns:
        User information.
    """
    return current_user
