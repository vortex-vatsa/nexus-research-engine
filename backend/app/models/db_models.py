"""SQLAlchemy ORM models for database persistence."""

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class User(Base):
    """Represents an authenticated user from Google OAuth."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    google_id: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<User(email={self.email}, name={self.name})>"


class Job(Base):
    """Represents a research job."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    user_email: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(20))  # pending/running/complete/failed
    progress_message: Mapped[str] = mapped_column(String(512), default="")
    workspace_slug: Mapped[str | None] = mapped_column(String(60))
    error: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<Job(id={self.id}, status={self.status}, "
            f"user={self.user_email})>"
        )
