"""FastAPI dependency injection for authentication."""

import logging

from fastapi import HTTPException, Request

from app.core.schemas import AuthUser

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> AuthUser:
    """Get the current authenticated user from session.

    Reads user data from request.session set by OAuth callback.
    Raises 401 if user is not authenticated.

    Args:
        request: FastAPI request object with session

    Returns:
        AuthUser with current user information

    Raises:
        HTTPException: 401 if not authenticated
    """
    user_data = request.session.get("user")

    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    try:
        return AuthUser(**user_data)
    except Exception as e:
        logger.error(f"Failed to parse user session: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid user session",
        )
