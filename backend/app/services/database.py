"""SQLAlchemy database engine and session management."""

import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.sql import text

from app.core.config import get_settings
from app.core.schemas import JobStatus
from app.models.db_models import Base

logger = logging.getLogger(__name__)


async def init_db():
    """Initialize database engine and create tables on startup."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")

    return engine


def get_async_session_maker():
    """Create async session factory."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    return async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )


async def create_tables():
    """Create all tables in the database.

    Creates tables if they don't exist. Safe to call multiple times.
    """
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
    finally:
        await engine.dispose()


async def get_db(session_maker=None):
    """FastAPI dependency that yields an async database session.

    Args:
        session_maker: Optional AsyncSessionMaker factory

    Yields:
        AsyncSession for database operations
    """
    if session_maker is None:
        session_maker = get_async_session_maker()

    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def heal_stale_jobs(db: AsyncSession):
    """Mark stale jobs as failed on application startup.

    Sets all RUNNING or PENDING jobs to FAILED with appropriate error message.
    This ensures jobs don't get stuck if the server crashes.

    Args:
        db: AsyncSession for database operations
    """
    try:
        # Query all running/pending jobs
        running_val = JobStatus.RUNNING.value
        pending_val = JobStatus.PENDING.value
        stale_jobs = await db.execute(
            text(
                f"SELECT id FROM jobs WHERE status IN "
                f"('{running_val}', '{pending_val}')"
            )
        )
        job_ids = [row[0] for row in stale_jobs.fetchall()]

        if job_ids:
            # Update them to failed
            for job_id in job_ids:
                await db.execute(
                    text(
                        f"UPDATE jobs SET status = '{JobStatus.FAILED.value}', "
                        f"error = 'Server restarted while job was in progress.' "
                        f"WHERE id = '{job_id}'"
                    )
                )
            await db.commit()
            logger.info(
                f"Healed {len(job_ids)} stale jobs from previous crash"
            )
    except Exception as e:
        logger.warning(f"Failed to heal stale jobs: {e}")
