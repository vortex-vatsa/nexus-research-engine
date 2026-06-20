"""Workspace CRUD API routes."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.config import email_to_slug
from app.core.schemas import AuthUser, DashboardPayload, WorkspaceListItem
from app.repository.workspace_repo import get_workspace_repo
from app.services.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_workspaces(
    current_user: AuthUser = Depends(get_current_user),
    workspace_repo=Depends(get_workspace_repo),
) -> list[WorkspaceListItem]:
    """List all workspaces for the current user.

    Args:
        current_user: Authenticated user from session
        workspace_repo: Workspace repository

    Returns:
        List of WorkspaceListItem sorted by recency
    """
    email_slug = email_to_slug(current_user.email)
    workspaces = await workspace_repo.list_workspaces(email_slug)
    logger.info(f"Listed {len(workspaces)} workspaces for {current_user.email}")
    return workspaces


@router.get("/{slug}")
async def get_workspace(
    slug: str,
    current_user: AuthUser = Depends(get_current_user),
    workspace_repo=Depends(get_workspace_repo),
) -> DashboardPayload:
    """Get a specific workspace by slug.

    Args:
        slug: Workspace slug
        current_user: Authenticated user from session
        workspace_repo: Workspace repository

    Returns:
        DashboardPayload with all workspace data
    """
    email_slug = email_to_slug(current_user.email)
    payload = await workspace_repo.load_payload(email_slug, slug)
    logger.info(f"Loaded workspace {slug} for {current_user.email}")
    return payload


@router.delete("/{slug}")
async def delete_workspace(
    slug: str,
    current_user: AuthUser = Depends(get_current_user),
    workspace_repo=Depends(get_workspace_repo),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a workspace and all its contents.

    Args:
        slug: Workspace slug
        current_user: Authenticated user from session
        workspace_repo: Workspace repository
        db: Database session

    Returns:
        Confirmation message
    """
    email_slug = email_to_slug(current_user.email)
    await workspace_repo.delete_workspace(email_slug, slug)
    logger.info(f"Deleted workspace {slug} for {current_user.email}")
    return {"status": "deleted", "slug": slug}


@router.get("/{slug}/sources/{source_id}")
async def get_workspace_source(
    slug: str,
    source_id: str,
    current_user: AuthUser = Depends(get_current_user),
    workspace_repo=Depends(get_workspace_repo),
) -> dict:
    """Get raw source document from a workspace.

    Args:
        slug: Workspace slug
        source_id: Source identifier (e.g., "src_0")
        current_user: Authenticated user from session
        workspace_repo: Workspace repository

    Returns:
        JSON with source content
    """
    email_slug = email_to_slug(current_user.email)
    content = await workspace_repo.load_source(email_slug, slug, source_id)
    logger.info(
        f"Loaded source {source_id} from workspace {slug} "
        f"for {current_user.email}"
    )
    return {"source_id": source_id, "content": content}
