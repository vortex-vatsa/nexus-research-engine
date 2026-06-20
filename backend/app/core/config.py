"""Configuration and environment settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # LLM
    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    OLLAMA_HOST: str | None = None

    # Search
    TAVILY_API_KEY: str

    # Auth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    ALLOWED_GOOGLE_EMAILS: str  # comma-separated: "user@gmail.com,other@gmail.com"
    SESSION_SECRET_KEY: str

    # Storage
    STORAGE_ROOT: str = "./storage"

    # Server
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    DATABASE_URL: str = "sqlite+aiosqlite:///./nexus.db"

    class Config:
        """Pydantic config for settings."""

        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_storage_path(email_slug: str, slug: str) -> Path:
    """Return Path(STORAGE_ROOT) / email_slug / slug.

    Never construct workspace paths from raw user input.
    Always use this function or WorkspaceRepository abstraction.
    """
    settings = get_settings()
    return Path(settings.STORAGE_ROOT) / email_slug / slug


def get_allowed_emails(settings: Settings) -> list[str]:
    """Parse ALLOWED_GOOGLE_EMAILS comma-separated string into list."""
    return [email.strip() for email in settings.ALLOWED_GOOGLE_EMAILS.split(",")]


def email_to_slug(email: str) -> str:
    """Convert email to safe directory name for use as storage path segment.

    Example: user@gmail.com → user_gmail_com
    Defined here (not in auth/) so orchestrator and repository can import it
    without circular dependencies.
    """
    return email.replace("@", "_").replace(".", "_")
