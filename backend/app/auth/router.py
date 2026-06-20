"""Google OAuth routes: login, callback, logout, me."""

import logging

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.core.config import get_allowed_emails, get_settings
from app.core.exceptions import AuthError
from app.core.schemas import AuthUser
from app.models.db_models import User

logger = logging.getLogger(__name__)

settings = get_settings()
oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url=(
        "https://accounts.google.com/.well-known/openid-configuration"
    ),
    client_kwargs={"scope": "openid email profile"},
)

router = APIRouter()


@router.get("/login")
async def login(request: Request):
    """Redirect user to Google OAuth authorization.

    Args:
        request: FastAPI request object

    Returns:
        Redirect response to Google OAuth authorization URL
    """
    redirect_uri = request.url_for("callback")
    logger.info(f"OAuth login initiated, redirect_uri: {redirect_uri}")
    return await oauth.google.authorize_redirect(request, str(redirect_uri))


@router.get("/callback")
async def callback(request: Request):
    """Handle Google OAuth callback.

    Validates token, extracts user info, checks email allowlist,
    upserts user in database, stores in session.

    Args:
        request: FastAPI request object with authorization code

    Returns:
        Redirect to frontend origin
    """
    try:
        # Exchange authorization code for token
        token = await oauth.google.authorize_access_token(request)
        userinfo = token.get("userinfo")

        if not userinfo:
            raise AuthError(
                "Failed to get user info from Google",
                context={"error": "No userinfo in token"},
            )

        email = userinfo.get("email")
        name = userinfo.get("name")
        picture = userinfo.get("picture")
        google_id = userinfo.get("sub")

        # Check email is allowed
        allowed_emails = get_allowed_emails(settings)
        if email not in allowed_emails:
            logger.warning(f"Access denied for email: {email}")
            raise AuthError(
                "Access denied",
                context={"email": email},
            )

        # Get or create user in database
        from app.services.database import get_async_session_maker
        session_maker = get_async_session_maker()
        async with session_maker() as db:
            user = await _upsert_user(
                db, google_id, email, name, picture
            )

        # Store in session
        request.session["user"] = {
            "google_id": user.google_id,
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar_url,
        }

        logger.info(f"User authenticated: {email}")

        # Redirect to frontend
        frontend_url = settings.FRONTEND_ORIGIN
        return {"redirect_url": frontend_url}

    except AuthError:
        raise
    except OAuthError as e:
        logger.error(f"OAuth error: {e}")
        raise AuthError(
            "OAuth authentication failed",
            context={"error": str(e)},
        )
    except Exception as e:
        logger.error(f"Callback error: {e}")
        raise AuthError(
            "Authentication callback failed",
            context={"error": str(e)},
        )


@router.get("/logout")
async def logout(request: Request):
    """Clear session and redirect to login page.

    Args:
        request: FastAPI request object

    Returns:
        JSON confirmation with redirect URL
    """
    request.session.clear()
    logger.info("User logged out")
    login_url = f"{settings.FRONTEND_ORIGIN}/login"
    return {"redirect_url": login_url}


@router.get("/me")
async def get_me(request: Request):
    """Get current authenticated user.

    Args:
        request: FastAPI request object with session

    Returns:
        AuthUser with current user information
    """
    user_data = request.session.get("user")

    if not user_data:
        return {"error": "Not authenticated"}, 401

    try:
        user = AuthUser(**user_data)
        return user
    except Exception as e:
        logger.error(f"Failed to parse user session: {e}")
        request.session.clear()
        return {"error": "Invalid user session"}, 401


async def _upsert_user(
    db: AsyncSession,
    google_id: str,
    email: str,
    name: str,
    avatar_url: str,
) -> User:
    """Create or update user in database.

    Args:
        db: Database session
        google_id: Google account ID
        email: User email
        name: User display name
        avatar_url: URL to profile picture

    Returns:
        User object from database
    """
    try:
        # Try to find existing user by email
        result = await db.execute(
            text(f"SELECT * FROM users WHERE email = '{email}'")
        )
        existing_user = result.fetchone()

        if existing_user:
            # Update existing user
            await db.execute(
                text(
                    f"UPDATE users SET name = '{name}', "
                    f"avatar_url = '{avatar_url}' WHERE email = '{email}'"
                )
            )
            await db.commit()
            logger.info(f"User updated: {email}")

            # Fetch updated user
            result = await db.execute(
                text(f"SELECT * FROM users WHERE email = '{email}'")
            )
            row = result.fetchone()
            return User(
                id=row[0],
                email=row[1],
                google_id=row[2],
                name=row[3],
                avatar_url=row[4],
            )
        else:
            # Create new user
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                avatar_url=avatar_url,
            )
            db.add(user)
            await db.commit()
            logger.info(f"New user created: {email}")
            return user

    except Exception as e:
        logger.error(f"Failed to upsert user: {e}")
        raise AuthError(
            "Failed to create/update user",
            context={"email": email, "error": str(e)},
        )
