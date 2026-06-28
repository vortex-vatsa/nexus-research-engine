"""Research orchestrator that coordinates the full research pipeline."""

import logging
import re
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.agents.researcher import ResearchAgent
from app.agents.synthesizer import SynthesizerAgent
from app.core.config import email_to_slug, get_settings
from app.core.exceptions import (
    ResearchAgentError,
    WorkspaceNotFoundError,
)
from app.core.schemas import JobStatus, ResearchJobStatus, ResearchRequest
from app.models.db_models import Job
from app.providers.llm_router import llm_router
from app.providers.search_client import TavilySearchClient
from app.repository.workspace_repo import workspace_repo
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


def slugify(topic: str) -> str:
    """Convert topic to a URL-safe slug.

    - Lowercase
    - Convert spaces to hyphens
    - Strip non-alphanumeric except hyphens
    - Collapse consecutive hyphens
    - Max 60 characters
    - Must match regex ^[a-z0-9-]+$

    Args:
        topic: Topic string

    Returns:
        Slugified topic

    Raises:
        ValueError: If slug is invalid after normalization
    """
    # Lowercase
    slug = topic.lower()

    # Convert spaces and underscores to hyphens
    slug = re.sub(r"[\s_]+", "-", slug)

    # Strip non-alphanumeric except hyphens
    slug = re.sub(r"[^a-z0-9-]", "", slug)

    # Collapse consecutive hyphens
    slug = re.sub(r"-+", "-", slug)

    # Strip leading/trailing hyphens
    slug = slug.strip("-")

    # Truncate to 60 chars
    slug = slug[:60]

    # Verify format
    if not re.match(r"^[a-z0-9-]+$", slug):
        raise ValueError(f"Invalid slug format: {slug}")

    return slug


def resolve_slug_collision(
    email_slug: str, slug: str, storage_root: str
) -> str:
    """Resolve slug collisions by appending -2, -3, etc.

    If {storage_root}/{email_slug}/{slug}/ exists, try
    {slug}-2, {slug}-3, etc. until an available slug is found.

    Args:
        email_slug: Email as safe directory name
        slug: Base slug
        storage_root: Storage root path

    Returns:
        Available slug (may be original or with -N suffix)
    """
    base_path = Path(storage_root) / email_slug / slug
    if not base_path.exists():
        return slug

    # Try with -2, -3, etc.
    counter = 2
    while counter < 100:
        candidate = f"{slug}-{counter}"
        candidate_path = Path(storage_root) / email_slug / candidate
        if not candidate_path.exists():
            return candidate
        counter += 1

    # Fallback with timestamp
    return f"{slug}-{uuid4().hex[:8]}"


class ResearchOrchestrator:
    """Orchestrates the full research pipeline from request to completion."""

    def __init__(self, settings, async_session_maker):
        """Initialize orchestrator.

        Args:
            settings: Application settings
            async_session_maker: AsyncSessionMaker factory
        """
        self.settings = settings
        self.async_session_maker = async_session_maker
        self.vector_store = VectorStoreService(settings)

    async def run_research(
        self, request: ResearchRequest, user_email: str, db: AsyncSession, job_id: str | None = None
    ) -> str:
        """Execute the full research pipeline.

        Steps:
        1. Create job record in database (if not pre-created)
        2. Generate search queries
        3. Search the web
        4. Synthesize findings
        5. Build vector knowledge base
        6. Mark job as complete

        Args:
            request: ResearchRequest with topic and preferences
            user_email: User email for workspace isolation
            db: AsyncSession for database operations
            job_id: Pre-generated job ID, or None to generate one

        Returns:
            Job ID for tracking

        Raises:
            ResearchAgentError: If any step fails
        """
        if job_id is None:
            job_id = str(uuid4())
        request_id = job_id[:8]
        email_slug = email_to_slug(user_email)

        # Slugify topic and resolve collisions
        try:
            base_slug = slugify(request.topic)
        except ValueError as e:
            raise ResearchAgentError(
                f"Invalid topic: {e}",
                context={"topic": request.topic},
            )

        slug = resolve_slug_collision(email_slug, base_slug, self.settings.STORAGE_ROOT)

        try:
            # Step 1: Create workspace directory
            await workspace_repo.ensure_workspace_dir(email_slug, slug)

            # Step 2: Insert job record (skip if already created by endpoint)
            logger.info(
                f"[{request_id}] Starting: {request.topic}"
            )

            # Step 3: Run researcher agent
            await self._update_job_status(
                db, job_id, JobStatus.RUNNING, "Generating search queries..."
            )

            async with TavilySearchClient(self.settings) as search_client:
                researcher = ResearchAgent(
                    request, slug, email_slug, llm_router, search_client, self.settings
                )
                sources = await researcher.run()

            logger.info(f"[{request_id}] Found {len(sources)} sources")

            # Step 4: Run synthesizer agent
            await self._update_job_status(
                db, job_id, JobStatus.RUNNING, "Synthesizing findings..."
            )

            synthesizer = SynthesizerAgent(
                request, slug, email_slug, llm_router, workspace_repo, self.settings
            )
            payload = await synthesizer.run(sources)
            logger.info(
                f"[{request_id}] Synthesized into {len(payload.matrix_data)} components"
            )

            # Step 5: Build vector knowledge base
            await self._update_job_status(
                db, job_id, JobStatus.RUNNING, "Building knowledge base..."
            )

            await self.vector_store.ingest(sources, email_slug, slug)
            logger.info(f"[{request_id}] Knowledge base built")

            # Step 6: Mark as complete
            await self._update_job_status(
                db,
                job_id,
                JobStatus.COMPLETE,
                "Research complete.",
                workspace_slug=slug,
            )

            logger.info(
                f"[{request_id}] Research complete: {slug} "
                f"({len(sources)} sources, {len(payload.matrix_data)} components)"
            )
            return job_id

        except Exception as e:
            # Mark job as failed
            logger.error(f"[{request_id}] Research failed: {e}")
            await self._update_job_status(
                db, job_id, JobStatus.FAILED, error=str(e)
            )
            raise

    async def get_job_status(
        self, job_id: str, user_email: str, db: AsyncSession
    ) -> ResearchJobStatus:
        """Get the status of a research job.

        Users can only see their own jobs.

        Args:
            job_id: Job ID to look up
            user_email: User email (for access control)
            db: AsyncSession for database operations

        Returns:
            ResearchJobStatus with current progress

        Raises:
            WorkspaceNotFoundError: If job not found or not owned by user
        """
        result = await db.execute(
            select(Job).where(
                (Job.id == job_id) & (Job.user_email == user_email)
            )
        )
        job = result.scalars().first()

        if not job:
            raise WorkspaceNotFoundError(
                "Job not found",
                context={"job_id": job_id, "user_email": user_email},
            )

        return ResearchJobStatus(
            job_id=job.id,
            status=job.status,
            progress_message=job.progress_message,
            workspace_slug=job.workspace_slug,
            error=job.error,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    async def _update_job_status(
        self,
        db: AsyncSession,
        job_id: str,
        status: JobStatus,
        message: str = "",
        workspace_slug: str = None,
        error: str = None,
    ):
        """Update job status in database.

        Args:
            db: AsyncSession for database operations
            job_id: Job ID to update
            status: New JobStatus
            message: Progress message
            workspace_slug: Workspace slug on completion
            error: Error message if failed
        """
        workspace_val = f"'{workspace_slug}'" if workspace_slug else "NULL"
        error_val = f"'{error}'" if error else "NULL"

        query = (
            f"UPDATE jobs SET status = '{status.value}', "
            f"progress_message = '{message}', "
            f"workspace_slug = {workspace_val}, "
            f"error = {error_val}, "
            f"updated_at = CURRENT_TIMESTAMP "
            f"WHERE id = '{job_id}'"
        )
        await db.execute(text(query))
        await db.commit()


# Module singleton
orchestrator = ResearchOrchestrator(
    get_settings(),
    None,  # Will be set in main.py after database initialization
)


def get_orchestrator() -> ResearchOrchestrator:
    """FastAPI dependency for research orchestrator.

    Returns:
        Module-level ResearchOrchestrator instance
    """
    return orchestrator
