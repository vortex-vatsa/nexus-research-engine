"""FastAPI dependency injection for authentication."""

import logging

from fastapi import HTTPException, Request
from jose import JWTError, jwt

from app.core.config import get_allowed_emails, get_settings
from app.core.schemas import AuthUser

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> AuthUser:
    """Get current user from JWT token in Authorization header.

    Validates JWT signature and email allowlist. Raises 401 if not authenticated.

    Args:
        request: FastAPI request object with Authorization header

    Returns:
        AuthUser with authenticated user information

    Raises:
        HTTPException: 401 if not authenticated or token invalid
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.split(" ")[1]
    settings = get_settings()

    try:
        payload = jwt.decode(
            token, settings.SESSION_SECRET_KEY, algorithms=["HS256"]
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Verify email is still in allowlist
        if email not in get_allowed_emails(settings):
            raise HTTPException(status_code=403, detail="Access denied")

        return AuthUser(
            google_id=payload.get("google_id", ""),
            email=email,
            name=payload.get("name", email.split("@")[0]),
            avatar_url=payload.get("avatar_url", ""),
        )
    except JWTError:
        logger.warning(f"Invalid JWT token")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
