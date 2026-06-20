"""Research API routes: run and status."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import get_orchestrator
from app.auth.dependencies import get_current_user
from app.core.schemas import AuthUser, ResearchJobStatus, ResearchRequest
from app.services.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run")
async def run_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    orchestrator=Depends(get_orchestrator),
) -> dict:
    """Start a new research job.

    Initiates research in the background and returns immediately
    with a job ID for tracking.

    Args:
        request: ResearchRequest with topic and preferences
        background_tasks: FastAPI background tasks
        current_user: Authenticated user from session
        db: Database session
        orchestrator: Research orchestrator

    Returns:
        JSON with job_id and status message
    """
    # Add research task to background
    background_tasks.add_task(
        orchestrator.run_research, request, current_user.email, db
    )

    logger.info(f"Research started for {current_user.email}: {request.topic}")
    return {
        "status": "accepted",
        "message": "Research job started. Check status endpoint for progress.",
    }


@router.get("/status/{job_id}")
async def get_research_status(
    job_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    orchestrator=Depends(get_orchestrator),
) -> ResearchJobStatus:
    """Get the status of a research job.

    Users can only see their own jobs.

    Args:
        job_id: Job ID to look up
        current_user: Authenticated user from session
        db: Database session
        orchestrator: Research orchestrator

    Returns:
        ResearchJobStatus with progress information
    """
    return await orchestrator.get_job_status(job_id, current_user.email, db)
